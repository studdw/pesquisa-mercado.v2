import asyncio
import time

import httpx

from ..core.config import get_settings
from ..models import PharmacyStatus, Product
from ..scrapers.base import BlockedError
from ..scrapers.registry import SCRAPERS
from .lab_matcher import LabMatcher, relevance
from .normalize import extract_concentration, extract_quantity, to_float
from .storage import get_storage

MIN_RELEVANCE = 80
matcher = LabMatcher()


def enrich(raw: dict, molecule: str, pharmacy_label: str) -> Product | None:
    name = (raw.get("name") or "").strip()
    score = relevance(name, molecule, matcher.brand_names_for(molecule))
    if not name or score < MIN_RELEVANCE:
        return None
    price, list_price = to_float(raw.get("price")), to_float(raw.get("list_price"))
    if list_price and price and list_price < price:
        list_price = None
    lab = matcher.identify(name, molecule, raw.get("brand"))
    qty = extract_quantity(name)
    return Product(
        pharmacy=pharmacy_label, molecule=molecule, name=name,
        price=price, list_price=list_price,
        discount_pct=round((1 - price / list_price) * 100, 1) if price and list_price and list_price > price else None,
        laboratory=lab.laboratory, lab_source=lab.source, lab_confidence=round(lab.confidence, 2),
        concentration=extract_concentration(name), quantity=qty,
        unit_price=round(price / qty, 4) if price and qty else None,
        ean=str(raw["ean"]) if raw.get("ean") else None, url=raw.get("url"),
        available=bool(raw.get("available", True)), match_score=round(score, 1),
    )


async def _one(client, key: str, molecule: str, force: bool):
    cls = SCRAPERS[key]
    storage = get_storage()
    cache_key = f"{key}:{molecule.lower().strip()}"
    if not force and (cached := storage.get_cache(cache_key)) is not None:
        prods = [Product(**p) for p in cached]
        return prods, PharmacyStatus(pharmacy=cls.label, ok=True, count=len(prods), cached=True)
    try:
        raw = await cls(client).search(molecule)
        prods = [p for r in raw if (p := enrich(r, molecule, cls.label))]
        # remove duplicados (mesmo nome) mantendo o menor preço
        best: dict[str, Product] = {}
        for p in prods:
            if p.name not in best or (p.price or 1e9) < (best[p.name].price or 1e9):
                best[p.name] = p
        prods = list(best.values())
        storage.set_cache(cache_key, [p.model_dump() for p in prods])
        storage.save_history([p.model_dump() for p in prods])
        return prods, PharmacyStatus(pharmacy=cls.label, ok=True, count=len(prods))
    except BlockedError as e:
        return [], PharmacyStatus(pharmacy=cls.label, ok=False, error=f"Bloqueado: {e}")
    except Exception as e:  # noqa: BLE001 - reportar qualquer falha sem derrubar as outras farmácias
        return [], PharmacyStatus(pharmacy=cls.label, ok=False, error=f"{type(e).__name__}: {str(e)[:150]}")


async def run_search(molecules: list[str], pharmacies: list[str], force: bool = False):
    s = get_settings()
    start = time.monotonic()
    molecules = list(dict.fromkeys(m.strip() for m in molecules if m.strip()))[: s.max_molecules_per_request]
    pharmacies = [p for p in pharmacies if p in SCRAPERS]
    async with httpx.AsyncClient(timeout=s.request_timeout, http2=False) as client:
        tasks = [_one(client, ph, mol, force) for mol in molecules for ph in pharmacies]
        done = await asyncio.gather(*tasks)
    results, statuses = [], {}
    for prods, st in done:
        results.extend(prods)
        agg = statuses.setdefault(st.pharmacy, PharmacyStatus(pharmacy=st.pharmacy, ok=True, cached=True))
        agg.count += st.count
        agg.cached = agg.cached and st.cached
        if not st.ok:
            agg.ok, agg.error = False, st.error
    results.sort(key=lambda p: (p.molecule, p.price or 1e9))
    return results, list(statuses.values()), round(time.monotonic() - start, 2)
