import asyncio
import json
import os

os.environ["API_KEY"] = "test"

from app.scrapers.html_generic import extract_structured
from app.scrapers.vtex import VtexScraper
from app.services.lab_matcher import LabMatcher, relevance
from app.services.normalize import extract_concentration, extract_quantity, to_float
from app.services.search import enrich

m = LabMatcher()


def test_lab_brand_wins():
    r = m.identify("Ozempic 1mg Caneta", "semaglutida", brand="NOVO NORDISK")
    assert r.laboratory == "Novo Nordisk" and r.source == "brand"


def test_lab_reference_for_branded_product():
    # caso que falhava no app antigo: produto de referência sem laboratório no título
    r = m.identify("Jardiance 25mg 30 Comprimidos", "empagliflozina")
    assert r.laboratory == "Boehringer Ingelheim" and r.source == "referencia"


def test_lab_title_for_generic():
    r = m.identify("Losartana Potássica 50mg 30 Comprimidos EMS Genérico", "losartana")
    assert r.laboratory == "EMS" and r.source == "titulo"


def test_lab_unknown():
    assert m.identify("Produto X 10mg", "xyz").laboratory == "Não identificado"


def test_normalize():
    assert extract_concentration("Losartana 50mg 30 comp") == "50mg"
    assert extract_quantity("Losartana 50mg 30 comprimidos") == 30
    assert extract_quantity("Glifage XR 500mg c/ 60") == 60
    assert to_float("R$ 1.234,56") == 1234.56


def test_relevance():
    assert relevance("Ozempic Semaglutida 1mg", "semaglutida") == 100
    assert relevance("Shampoo anticaspa", "semaglutida") < 80


def test_enrich_unit_price_and_discount():
    p = enrich({"name": "Losartana 50mg 30 Comprimidos Medley", "price": 15.0, "list_price": 30.0},
               "losartana", "Teste")
    assert p.unit_price == 0.5 and p.discount_pct == 50.0 and p.laboratory == "Medley"


def test_extract_jsonld_and_next_data():
    ld = {"@type": "ItemList", "itemListElement": [
        {"@type": "Product", "name": "Jardiance 10mg 30 comp", "brand": {"name": "Boehringer"},
         "offers": {"price": "189.90"}, "url": "/jardiance-10mg"}]}
    nd = {"props": {"pageProps": {"products": [{"productName": "Empagliflozina 25mg", "finalPrice": 99.5}]}}}
    html = (f'<script type="application/ld+json">{json.dumps(ld)}</script>'
            f'<script id="__NEXT_DATA__">{json.dumps(nd)}</script>')
    items = extract_structured(html)
    assert {i["name"] for i in items} == {"Jardiance 10mg 30 comp", "Empagliflozina 25mg"}


def test_vtex_parse():
    p = {"productName": "Ozempic", "brand": "Novo Nordisk", "link": "https://x/ozempic/p",
         "items": [{"nameComplete": "Ozempic 1mg Caneta", "ean": "789",
                    "sellers": [{"commertialOffer": {"Price": 900.0, "ListPrice": 1000.0, "IsAvailable": True}}]}]}
    out = VtexScraper.__new__(VtexScraper)._parse(p)
    assert out[0]["price"] == 900.0 and out[0]["brand"] == "Novo Nordisk"


def test_api_auth_and_health():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        assert c.get("/health").status_code == 200
        assert c.post("/search", json={"molecules": ["a"], "pharmacies": ["pacheco"]}).status_code == 401


def test_search_flow_end_to_end(monkeypatch, tmp_path):
    """Simula duas farmácias: uma responde, outra é bloqueada por captcha."""
    from app.scrapers import registry
    from app.scrapers.base import BlockedError
    from app.services import search as svc, storage

    monkeypatch.setattr(storage, "_SQLITE", tmp_path / "t.db")
    monkeypatch.setattr(storage, "_storage", None)

    async def ok(self, mol):
        return [
            {"name": "Jardiance 25mg 30 Comprimidos", "price": 180.0, "list_price": 200.0},
            {"name": "Empagliflozina 25mg 30 comprimidos EMS", "price": 90.0},
            {"name": "Protetor Solar FPS 50", "price": 50.0},  # irrelevante: deve ser descartado
        ]

    async def blocked(self, mol):
        raise BlockedError("captcha detectado")

    monkeypatch.setattr(registry.SCRAPERS["pacheco"], "search", ok)
    monkeypatch.setattr(registry.SCRAPERS["drogaraia"], "search", blocked)

    res, status, _ = asyncio.run(svc.run_search(["empagliflozina"], ["pacheco", "drogaraia"]))
    assert [r.laboratory for r in res] == ["EMS", "Boehringer Ingelheim"]
    st = {s.pharmacy: s for s in status}
    assert st["Drogarias Pacheco"].ok and not st["Drogaraia"].ok

    # segunda busca vem do cache
    _, status2, _ = asyncio.run(svc.run_search(["empagliflozina"], ["pacheco"]))
    assert status2[0].cached
    assert storage.get_storage().history("empagliflozina")
