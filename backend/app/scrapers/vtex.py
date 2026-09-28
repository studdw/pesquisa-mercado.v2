"""
Conector genérico para farmácias em VTEX. A API pública de catálogo devolve JSON
estruturado com 'brand' (laboratório) e EAN — muito mais confiável que ler HTML,
e raramente aciona captcha.
"""
from urllib.parse import quote

from .base import BaseScraper, RawItem


class VtexScraper(BaseScraper):
    base_url: str = ""
    page_size: int = 40

    async def search(self, molecule: str) -> list[RawItem]:
        await self.throttle()
        url = (
            f"{self.base_url}/api/catalog_system/pub/products/search"
            f"?ft={quote(molecule)}&_from=0&_to={self.page_size - 1}"
        )
        resp = await self.client.get(url, headers={**self.headers(), "Accept": "application/json"})
        self.check_blocked(resp)
        if resp.status_code not in (200, 206):
            raise RuntimeError(f"HTTP {resp.status_code}")
        return [i for p in resp.json() for i in self._parse(p)]

    def _parse(self, p: dict) -> list[RawItem]:
        out = []
        for item in p.get("items", [])[:3]:
            sellers = item.get("sellers") or [{}]
            offer = sellers[0].get("commertialOffer", {}) or {}
            out.append(RawItem(
                name=item.get("nameComplete") or p.get("productName", ""),
                price=offer.get("Price"),
                list_price=offer.get("ListPrice"),
                brand=p.get("brand"),
                ean=item.get("ean"),
                url=p.get("link"),
                available=bool(offer.get("IsAvailable", True)),
            ))
        return out


class DrogariaSaoPaulo(VtexScraper):
    key, label, base_url = "drogariasaopaulo", "Drogaria São Paulo", "https://www.drogariasaopaulo.com.br"


class Pacheco(VtexScraper):
    key, label, base_url = "pacheco", "Drogarias Pacheco", "https://www.drogariaspacheco.com.br"


class PagueMenos(VtexScraper):
    key, label, base_url = "paguemenos", "Pague Menos", "https://www.paguemenos.com.br"
