from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.security import require_api_key
from .models import SearchRequest, SearchResponse
from .scrapers.registry import SCRAPERS
from .services.search import run_search
from .services.storage import get_storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_storage()
    yield
    if get_settings().enable_browser:
        from .scrapers.browser import shutdown
        await shutdown()


app = FastAPI(title="Pesquisa de Preços por Molécula API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    """Público — usado pelo frontend para 'acordar' o Render e pelo ping do GitHub Actions."""
    return {"status": "ok", "browser": get_settings().enable_browser}


@app.get("/pharmacies", dependencies=[Depends(require_api_key)])
async def pharmacies():
    s = get_settings()
    return [
        {"key": k, "label": c.label, "requires_browser": c.requires_browser,
         "enabled": s.enable_browser or not c.requires_browser}
        for k, c in SCRAPERS.items()
    ]


@app.post("/search", response_model=SearchResponse, dependencies=[Depends(require_api_key)])
async def search(req: SearchRequest):
    results, status, elapsed = await run_search(req.molecules, req.pharmacies, req.force_refresh)
    return SearchResponse(results=results, status=status, elapsed_s=elapsed)


@app.get("/history", dependencies=[Depends(require_api_key)])
async def history(molecule: str = Query(min_length=2)):
    return get_storage().history(molecule)
