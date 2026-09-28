import secrets
from fastapi import Header, HTTPException, status
from .config import get_settings


async def require_api_key(x_api_key: str = Header(default="")) -> None:
    """Somente o proxy do Next.js (servidor Vercel) conhece a chave."""
    if not secrets.compare_digest(x_api_key, get_settings().api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida")
