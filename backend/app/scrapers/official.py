"""
Fonte oficial (Anvisa/CMED) — entra no mesmo fluxo de busca das farmácias,
mas NÃO faz scraping: lê a Lista de Preços de Medicamentos publicada pela Anvisa.
PMC = preço máximo que a farmácia pode cobrar (teto), não preço praticado.
"""
from .base import BaseScraper, RawItem
from ..core.config import get_settings
from ..services.cmed import CmedCatalog

_catalog: CmedCatalog | None = None


def get_catalog() -> CmedCatalog:
    global _catalog
    if _catalog is None:
        _catalog = CmedCatalog()
    return _catalog


class CmedAnvisa(BaseScraper):
    key, label = "cmed", "CMED/Anvisa (PMC)"

    async def search(self, molecule: str) -> list[RawItem]:
        cat = get_catalog()
        if not cat.available:
            raise RuntimeError(
                "Lista CMED não encontrada. Baixe o XLS em gov.br/anvisa (CMED > Preços de "
                "medicamentos) e salve como backend/data/cmed.xlsx"
            )
        icms = get_settings().cmed_icms
        return [
            RawItem(
                name=f"{i.product} {i.presentation}".strip(),
                price=i.pmc,              # teto ao consumidor
                list_price=None,
                brand=i.laboratory,       # laboratório oficial: matching 100% confiável
                ean=i.ean,
                url="https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos",
                available=True,
            )
            for i in cat.search(molecule, icms=icms)
            if i.pmc
        ]
