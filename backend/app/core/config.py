from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações lidas de variáveis de ambiente (Render > Environment)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str = "dev-key-troque-isto"          # chave compartilhada com o frontend (Vercel)
    allowed_origins: str = "http://localhost:3000"  # separadas por vírgula
    database_url: str = ""                          # vazio = SQLite local (efêmero no Render)
    cache_ttl_hours: float = 8.0                    # plano: cache de 6-12h
    enable_browser: bool = False                    # liga scrapers com Playwright (exige Docker)
    request_timeout: float = 30.0
    min_delay: float = 0.8                          # rate limiting entre requisições por farmácia
    max_delay: float = 2.0
    max_molecules_per_request: int = 15

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
