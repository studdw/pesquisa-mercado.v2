"""
Fonte oficial: Lista de Preços de Medicamentos da CMED/Anvisa.
Não é scraping: lê a planilha pública publicada mensalmente pela Anvisa
(https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos).

Arquivo esperado em backend/data/cmed.xlsx (ou .xls).
Fornece PF (Preço Fábrica) e PMC (Preço Máximo ao Consumidor) por alíquota de ICMS.
"""
from __future__ import annotations

import glob
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[2] / "data"
DEFAULT_ICMS = "18"  # São Paulo


def _n(s) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def _to_float(v) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = re.sub(r"[^\d,.]", "", str(v))
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        f = float(s)
        return f if f > 0 else None
    except ValueError:
        return None


def _find_header(raw: pd.DataFrame) -> int:
    """A planilha da CMED tem ~30 linhas de texto legal antes do cabeçalho real."""
    for i in range(min(80, len(raw))):
        row = " | ".join(_n(c) for c in raw.iloc[i].tolist())
        if "substancia" in row and ("produto" in row or "apresentacao" in row):
            return i
    raise ValueError("cabeçalho da planilha CMED não encontrado")


@dataclass
class CmedItem:
    substance: str
    product: str
    presentation: str
    laboratory: str
    kind: str          # tipo de produto (Genérico/Similar/Novo/Biológico)
    ean: str | None
    pf: float | None
    pmc: float | None
    icms: str
    tarja: str | None
    register: str | None


class CmedCatalog:
    """Carrega a lista CMED uma vez e responde buscas por substância/produto."""

    def __init__(self, path: Path | None = None):
        self.df: pd.DataFrame | None = None
        self.path = path or self._discover()
        self.competencia: str | None = None
        self._cols: dict = {}
        if self.path and self.path.exists():
            self._load()

    @staticmethod
    def _discover() -> Path | None:
        for pat in ("cmed*.xlsx", "cmed*.xls", "*cmed*.xlsx"):
            hits = sorted(glob.glob(str(DATA / pat)))
            if hits:
                return Path(hits[-1])
        return None

    @property
    def available(self) -> bool:
        return self.df is not None and not self.df.empty

    def _pick(self, *patterns: str) -> str | None:
        for p in patterns:
            for col in self.df.columns:
                if re.search(p, _n(col)):
                    return col
        return None

    def _load(self) -> None:
        engine = "xlrd" if self.path.suffix.lower() == ".xls" else "openpyxl"
        raw = pd.read_excel(self.path, header=None, nrows=80, engine=engine, dtype=str)
        hdr = _find_header(raw)
        self.df = pd.read_excel(self.path, header=hdr, engine=engine, dtype=str)
        self.df = self.df.dropna(how="all")
        c = self._cols
        c["substance"] = self._pick(r"^substancia")
        c["product"] = self._pick(r"^produto")
        c["presentation"] = self._pick(r"apresentacao")
        c["lab"] = self._pick(r"laboratorio")
        c["kind"] = self._pick(r"tipo de produto")
        c["ean"] = self._pick(r"^ean ?1", r"^ean")
        c["pf"] = self._pick(r"^pf ?18", r"^pf sem impostos")
        c["tarja"] = self._pick(r"tarja")
        c["register"] = self._pick(r"^registro")
        c["pmc"] = {}
        for col in self.df.columns:
            m = re.match(r"pmc ?(\d+(?:[.,]\d+)?) ?%", _n(col))
            if m:
                key = m.group(1).replace(",", ".")
                if "." in key:                      # 17.50 -> 17.5 ; 17.0 -> 17
                    key = key.rstrip("0").rstrip(".")
                c["pmc"][key or "0"] = col
        # índice normalizado para busca
        self._idx_sub = self.df[c["substance"]].fillna("").map(_n) if c["substance"] else None
        self._idx_prod = self.df[c["product"]].fillna("").map(_n) if c["product"] else None
        self.competencia = self.path.stem

    def icms_options(self) -> list[str]:
        return sorted(self._cols.get("pmc", {}), key=lambda x: float(x))

    def search(self, term: str, icms: str = DEFAULT_ICMS, limit: int = 300) -> list[CmedItem]:
        if not self.available:
            return []
        t = _n(term)
        if not t:
            return []
        mask = self._idx_sub.str.contains(t, regex=False, na=False)
        if self._idx_prod is not None:
            mask |= self._idx_prod.str.contains(t, regex=False, na=False)
        rows = self.df[mask].head(limit)
        c = self._cols
        pmc_col = c["pmc"].get(icms) or c["pmc"].get(DEFAULT_ICMS) or (list(c["pmc"].values()) or [None])[0]
        out = []
        for _, r in rows.iterrows():
            ean = str(r.get(c["ean"]) or "").strip() if c["ean"] else None
            out.append(CmedItem(
                substance=str(r.get(c["substance"]) or "").strip(),
                product=str(r.get(c["product"]) or "").strip(),
                presentation=str(r.get(c["presentation"]) or "").strip(),
                laboratory=str(r.get(c["lab"]) or "").strip(),
                kind=str(r.get(c["kind"]) or "").strip(),
                ean=ean if ean and ean.lower() != "nan" else None,
                pf=_to_float(r.get(c["pf"])) if c["pf"] else None,
                pmc=_to_float(r.get(pmc_col)) if pmc_col else None,
                icms=icms,
                tarja=str(r.get(c["tarja"]) or "").strip() or None if c["tarja"] else None,
                register=str(r.get(c["register"]) or "").strip() or None if c["register"] else None,
            ))
        return out
