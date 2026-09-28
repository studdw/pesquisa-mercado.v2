"""Normalização de textos, concentração e quantidade para comparação 'maçã com maçã'."""
import re
import unicodedata

_CONC = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mcg|µg|mg|g|ui|mg/ml|mg/g|%)\b", re.I)
_QTY = re.compile(
    r"(\d{1,4})\s*(?:comprimidos?|comp\.?|cpr|caps(?:ulas?)?|cáps(?:ulas?)?|drágeas?|unid(?:ades)?|un\b|sachês?|ampolas?|canetas?)",
    re.I,
)
_QTY_X = re.compile(r"\b(?:c/|com|x)\s*(\d{1,4})\b", re.I)


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def norm(text: str | None) -> str:
    if not text:
        return ""
    t = strip_accents(text).lower()
    t = re.sub(r"[^a-z0-9%/.,+ ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def extract_concentration(name: str) -> str | None:
    found = _CONC.findall(name or "")
    if not found:
        return None
    return " + ".join(f"{v.replace(',', '.')}{u.lower().replace('µg', 'mcg')}" for v, u in found)


def extract_quantity(name: str) -> int | None:
    m = _QTY.search(name or "") or _QTY_X.search(name or "")
    if m:
        q = int(m.group(1))
        return q if 0 < q < 2000 else None
    return None


def to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    s = re.sub(r"[^\d,.]", "", str(value))
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        v = float(s)
        return v if v > 0 else None
    except ValueError:
        return None
