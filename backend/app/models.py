from pydantic import BaseModel, Field


class Product(BaseModel):
    pharmacy: str
    molecule: str
    name: str
    price: float | None = None
    list_price: float | None = None
    discount_pct: float | None = None
    laboratory: str = "Não identificado"
    lab_source: str = "nenhum"      # brand | referencia | titulo | nenhum
    lab_confidence: float = 0.0
    concentration: str | None = None
    quantity: int | None = None
    unit_price: float | None = None
    ean: str | None = None
    url: str | None = None
    available: bool = True
    match_score: float = 0.0        # relevância do produto para a molécula


class PharmacyStatus(BaseModel):
    pharmacy: str
    ok: bool
    count: int = 0
    cached: bool = False
    error: str | None = None


class SearchRequest(BaseModel):
    molecules: list[str] = Field(min_length=1)
    pharmacies: list[str] = Field(min_length=1)
    force_refresh: bool = False


class SearchResponse(BaseModel):
    results: list[Product]
    status: list[PharmacyStatus]
    elapsed_s: float
