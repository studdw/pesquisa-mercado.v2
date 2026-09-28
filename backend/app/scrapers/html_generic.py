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

import re

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

def extract_ultrafarma(html: str, base_url: str = "https://www.ultrafarma.com.br") -> list:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for card in soup.select("div.product-item[data-product-id]"):
        name = card.get("data-product-name", "").strip()
        try:
            price = float(card.get("data-product-price", "").replace(",", "."))  # ex.: "2.690"
        except ValueError:
            price = None
        list_price = None
        old = card.select_one(".product-item-old-price [data-preco]")
        if old:
            try:
                list_price = float(old["data-preco"].replace(".", "").replace(",", "."))  # ex.: "10,560"
            except ValueError:
                pass
        a = card.select_one("a.product-item-link[href]")
        href = a["href"] if a else None
        if href and not href.startswith("http"):
            href = base_url.rstrip("/") + "/" + href.lstrip("/")
        classes = " ".join(a.get("class", [])) if a else ""
        if name and price:
            out.append(RawItem(
                name=name, price=price, list_price=list_price,
                brand=card.get("data-product-brand"),   # laboratório (ex.: "GERMED GENÉRICO")
                ean=None, url=href, available="unavailable" not in classes,
            ))
    return out

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
            items = extract_structured(resp.text) or extract_cards(resp.text, self.base_url)
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

    async def search(self, molecule: str) -> list:
        await self.throttle()
        url = self.search_url.format(q=quote(molecule))
        resp = await self.client.get(url, headers=self.headers(), follow_redirects=True)
        self.check_blocked(resp)
        return extract_ultrafarma(resp.text, self.base_url)

_PRICE = r"R\$\s*([\d.]+,\d{2})"
_POR = re.compile(r"\bPor\s*" + _PRICE, re.I)
_DE = re.compile(r"\bDe\s*" + _PRICE, re.I)


def _num(s):
    return float(s.replace(".", "").replace(",", "."))


def extract_cards(html: str, base_url: str = "") -> list:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg"]):
        t.decompose()
    cards, seen = [], set()
    for node in soup.find_all(string=re.compile(r"R\$")):
        el = node.parent
        for _ in range(10):
            if el is None or el.name in ("body", "html"):
                el = None
                break
            text = el.get_text(" ", strip=True)
            if len(_POR.findall(text)) > 1:   # subiu demais: bloco com vários produtos
                el = None
                break
            if _POR.search(text) and el.find("a", href=True):
                break
            el = el.parent
        if el is None or id(el) in seen:
            continue
        seen.add(id(el))
        text = el.get_text(" ", strip=True)
        m = _POR.search(text)
        cand = []
        for a in el.find_all("a", href=True):
            cand += [a.get("title") or "", a.get_text(" ", strip=True)]
        cand += [img.get("alt") or "" for img in el.find_all("img")]
        cand += [h.get_text(" ", strip=True) for h in el.find_all(["h2", "h3", "h4"])]
        cand = [c for c in cand if len(c) > 8 and "R$" not in c]
        if not m or not cand:
            continue
        link = next((a["href"] for a in el.find_all("a", href=True) if a["href"] not in ("#", "")), None)
        if link and not link.startswith("http"):
            link = base_url.rstrip("/") + "/" + link.lstrip("/")
        de = _DE.search(text)
        cards.append(RawItem(name=max(cand, key=len), price=_num(m.group(1)),
                             list_price=_num(de.group(1)) if de else None,
                             brand=None, ean=None, url=link, available=True))
    uniq, keys = [], set()
    for c in cards:
        k = (c["name"].lower(), c["price"])
        if k not in keys:
            keys.add(k)
            uniq.append(c)
    return uniq