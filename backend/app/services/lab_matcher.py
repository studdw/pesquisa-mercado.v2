"""
Identificação de laboratório em 3 camadas (corrige a falha do projeto antigo,
que só funcionava para genéricos porque dependia do título):

1. brand/manufacturer estruturado vindo da própria farmácia (VTEX / JSON-LD)
2. base de referência produto -> molécula -> laboratório (data/referencia_laboratorios.csv)
   com fuzzy matching (RapidFuzz)
3. laboratório citado no título (caso típico dos genéricos)
Se nada bater, retorna 'Não identificado' em vez de errar silenciosamente.
"""
import csv
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz, process

from .normalize import norm

DATA = Path(__file__).resolve().parents[2] / "data"

# Aliases para padronizar nomes de laboratório vindos de fontes diferentes
LAB_ALIASES: dict[str, str] = {
    "ems": "EMS", "ems sigma pharma": "EMS", "germed": "Germed", "legrand": "Legrand",
    "eurofarma": "Eurofarma", "medley": "Medley", "sanofi medley": "Medley",
    "neo quimica": "Neo Química", "neoquimica": "Neo Química", "hypera": "Hypera",
    "ache": "Aché", "libbs": "Libbs", "biolab": "Biolab", "biolab sanus": "Biolab",
    "torrent": "Torrent", "sandoz": "Sandoz", "novartis": "Novartis", "pfizer": "Pfizer",
    "viatris": "Viatris", "mylan": "Viatris", "teuto": "Teuto", "prati donaduzzi": "Prati-Donaduzzi",
    "prati": "Prati-Donaduzzi", "cimed": "Cimed", "merck": "Merck", "msd": "MSD",
    "astrazeneca": "AstraZeneca", "novo nordisk": "Novo Nordisk", "eli lilly": "Eli Lilly",
    "lilly": "Eli Lilly", "boehringer": "Boehringer Ingelheim", "boehringer ingelheim": "Boehringer Ingelheim",
    "bayer": "Bayer", "abbott": "Abbott", "gsk": "GSK", "glaxosmithkline": "GSK",
    "sanofi": "Sanofi", "takeda": "Takeda", "servier": "Servier", "zydus": "Zydus",
    "ranbaxy": "Sun Pharma", "sun pharma": "Sun Pharma", "cristalia": "Cristália",
    "uniao quimica": "União Química", "apsen": "Apsen", "mantecorp": "Mantecorp",
    "brainfarma": "Neo Química", "natcofarma": "Natcofarma", "multilab": "Multilab",
    "geolab": "Geolab", "vitamedic": "Vitamedic", "nova quimica": "Nova Química",
    "sanval": "Sanval", "globo": "Globo", "belfar": "Belfar", "ranbaxy farma": "Sun Pharma",
    "dr reddys": "Dr. Reddy's", "dr. reddys": "Dr. Reddy's", "accord": "Accord", "fqm": "FQM",
}

# Marcas que são da própria farmácia/genéricas sem valor de laboratório
_NOT_LABS = {"generico", "genericos", "similar", "referencia", "drogasil", "raia", "ultrafarma"}


@dataclass
class LabResult:
    laboratory: str
    source: str
    confidence: float


def canonical_lab(raw: str | None) -> str | None:
    n = norm(raw)
    if not n or n in _NOT_LABS:
        return None
    if n in LAB_ALIASES:
        return LAB_ALIASES[n]
    best = process.extractOne(n, LAB_ALIASES.keys(), scorer=fuzz.token_set_ratio)
    if best and best[1] >= 90:
        return LAB_ALIASES[best[0]]
    return raw.strip().title() if len(n) >= 3 else None


class LabMatcher:
    def __init__(self, reference_csv: Path | None = None):
        self.rows: list[dict] = []
        self._keys: list[str] = []
        path = reference_csv or DATA / "referencia_laboratorios.csv"
        if path.exists():
            with path.open(encoding="utf-8-sig") as f:
                for r in csv.DictReader(f, delimiter=";"):
                    if r.get("produto") and r.get("laboratorio"):
                        self.rows.append(r)
                        self._keys.append(norm(r["produto"]))

    def _from_reference(self, name: str, molecule: str) -> LabResult | None:
        if not self.rows:
            return None
        n = norm(name)
        mol = norm(molecule)
        # Restringe aos registros da mesma molécula quando possível
        idx = [i for i, r in enumerate(self.rows) if mol and mol in norm(r.get("molecula", ""))] or range(len(self.rows))
        choices = {i: self._keys[i] for i in idx}
        best = process.extractOne(n, choices, scorer=fuzz.partial_token_set_ratio)
        if best and best[1] >= 88:
            row = self.rows[best[2]]
            return LabResult(canonical_lab(row["laboratorio"]) or row["laboratorio"], "referencia", best[1] / 100)
        return None

    @staticmethod
    def _from_title(name: str) -> LabResult | None:
        n = f" {norm(name)} "
        # procura o alias mais longo primeiro (ex.: 'neo quimica' antes de 'ems')
        for alias in sorted(LAB_ALIASES, key=len, reverse=True):
            if f" {alias} " in n:
                return LabResult(LAB_ALIASES[alias], "titulo", 0.8)
        return None

    def identify(self, name: str, molecule: str, brand: str | None = None) -> LabResult:
        lab = canonical_lab(brand)
        if lab:
            return LabResult(lab, "brand", 0.95)
        return (
            self._from_reference(name, molecule)
            or self._from_title(name)
            or LabResult("Não identificado", "nenhum", 0.0)
        )


    def brand_names_for(self, molecule: str) -> list[str]:
        """Nomes comerciais conhecidos da molécula (ex.: empagliflozina -> jardiance)."""
        mol = norm(molecule)
        return [self._keys[i] for i, r in enumerate(self.rows) if mol and mol in norm(r.get("molecula", ""))]


def relevance(name: str, molecule: str, brand_names: list[str] | None = None) -> float:
    """Score 0-100 de quanto o produto corresponde à molécula pesquisada.
    Considera também os nomes comerciais da base de referência, para não descartar
    produtos de marca que não citam a molécula no título (ex.: Jardiance)."""
    n, m = norm(name), norm(molecule)
    if not m:
        return 0.0
    if all(tok in n for tok in m.split()):
        return 100.0
    if brand_names and any(f" {b} " in f" {n} " for b in brand_names):
        return 100.0
    return float(fuzz.partial_token_set_ratio(m, n))
