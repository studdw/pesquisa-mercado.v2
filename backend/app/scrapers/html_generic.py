"""
Conector para sites que não expõem API (ex.: Drogaraia, Ultrafarma).
Estratégia em camadas, da mais barata para a mais cara:
  1. httpx + extração de dados estruturados (JSON-LD schema.org / __NEXT_DATA__)
  2. se bloqueado ou vazio e ENABLE_BROWSER=true: Playwright + stealth
Extrair JSON embutido é bem mais estável que depender de seletores CSS,
que quebram a cada redesign do site.
"""
import json
from urllib.parse import quote

from bs4 import BeautifulSoup

from .base import BaseScraper, BlockedError, RawItem
from ..services.normalize import to_float

NAME_KEYS = ("name", "productName", "nome", "title")
PRICE_KEYS = ("price", "finalPrice", "salePrice", "valuePrice", "bestPrice", "lowPrice", "preco", "priceFinal")
LIST_KEYS = ("listPrice", "regularPrice", "originalPrice", "fromPrice", "highPrice", "oldPrice")
BRAND_KEYS = ("brand", "manufacturer", "laboratory", "laboratorio", "fabricante", "brandName")
URL_KEYS = ("url", "link", "urlKey", "href", "slug")


def _brand(v):
    if isinstance(v, dict):
        return v.get("name")
    return v if isinstance(v, str) else None


def _walk(node, out: list, depth=0):
    """Varre JSON arbitrário procurando objetos com cara de produto (nome + preço)."""
    if depth > 14 or len(out) > 200:
        return
    if isinstance(node, dict):
        name = next((node[k] for k in NAME_KEYS if isinstance(node.get(k), str)), None)
        price = next((node[k] for k in PRICE_KEYS if node.get(k) not in (None, "", 0)), None)
        offers = node.get("offers")
        if price is None and isinstance(offers, dict):
            price = offers.get("price") or offers.get("lowPrice")
        if isinstance(price, dict):
            price = price.get("value") or price.get("amount")
        if name and to_float(price):
            out.append(RawItem(
                name=name,
                price=to_float(price),
                list_price=to_float(next((node[k] for k in LIST_KEYS if node.get(k)), None)),
                brand=next((_brand(node[k]) for k in BRAND_KEYS if node.get(k)), None),
                ean=node.get("gtin13") or node.get("ean") or node.get("gtin"),
                url=next((node[k] for k in URL_KEYS if isinstance(node.get(k), str)), None),
                available=True,
            ))
        for v in node.values():
            _walk(v, out, depth + 1)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out, depth + 1)


def extract_structured(html: str) -> list[RawItem]:
    soup = BeautifulSoup(html, "html.parser")
    blobs = [s.string for s in soup.find_all("script", type="application/ld+json") if s.string]
    nd = soup.find("script", id="__NEXT_DATA__")
    if nd and nd.string:
        blobs.append(nd.string)
    items: list[RawItem] = []
    for b in blobs:
        try:
            _walk(json.loads(b), items)
        except (json.JSONDecodeError, TypeError):
            continue
    # dedup por nome+preço
    seen, uniq = set(), []
    for i in items:
        k = (i["name"].lower(), i["price"])
        if k not in seen:
            seen.add(k)
            uniq.append(i)
    return uniq


class HtmlScraper(BaseScraper):
    search_url: str = ""   # com {q}
    base_url: str = ""

    async def search(self, molecule: str) -> list[RawItem]:
        url = self.search_url.format(q=quote(molecule))
        items: list[RawItem] = []
        blocked: Exception | None = None
        try:
            await self.throttle()
            resp = await self.client.get(url, headers=self.headers(), follow_redirects=True)
            self.check_blocked(resp)
            items = extract_structured(resp.text)
        except BlockedError as e:
            blocked = e

        if not items and self.settings.enable_browser:
            from .browser import fetch_rendered
            html = await fetch_rendered(url)
            items = extract_structured(html)
        elif not items and blocked:
            raise BlockedError(f"{blocked} (ative ENABLE_BROWSER para usar Playwright)")

        for i in items:
            if i.get("url") and not str(i["url"]).startswith("http"):
                i["url"] = self.base_url.rstrip("/") + "/" + str(i["url"]).lstrip("/")
        return items


class DrogaRaia(HtmlScraper):
    key, label = "drogaraia", "Drogaraia"
    base_url = "https://www.drogaraia.com.br"
    search_url = "https://www.drogaraia.com.br/search?w={q}"


class Ultrafarma(HtmlScraper):
    key, label = "ultrafarma", "Ultrafarma"
    base_url = "https://www.ultrafarma.com.br"
    search_url = "https://www.ultrafarma.com.br/busca?q={q}"
