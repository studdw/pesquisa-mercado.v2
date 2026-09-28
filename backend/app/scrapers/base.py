import asyncio
import random
import time
from abc import ABC, abstractmethod

import httpx

from ..core.config import get_settings

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
]


class BlockedError(Exception):
    """Site devolveu captcha/403/429 — sinaliza para tentar fallback (browser) ou reportar."""


class RawItem(dict):
    """name, price, list_price, brand, ean, url, available"""


class BaseScraper(ABC):
    key: str = ""
    label: str = ""
    requires_browser: bool = False

    # rate limiting por farmácia: 1 requisição por vez + delay aleatório
    _locks: dict[str, asyncio.Lock] = {}
    _last_call: dict[str, float] = {}

    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.settings = get_settings()

    def headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.6",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        }

    async def throttle(self) -> None:
        lock = self._locks.setdefault(self.key, asyncio.Lock())
        async with lock:
            wait = random.uniform(self.settings.min_delay, self.settings.max_delay)
            elapsed = time.monotonic() - self._last_call.get(self.key, 0)
            if elapsed < wait:
                await asyncio.sleep(wait - elapsed)
            self._last_call[self.key] = time.monotonic()

    @staticmethod
    def check_blocked(resp: httpx.Response) -> None:
        if resp.status_code in (403, 429, 503):
            raise BlockedError(f"HTTP {resp.status_code}")
        body = resp.text[:4000].lower()
        if any(s in body for s in ("g-recaptcha", "hcaptcha", "cf-challenge", "are you a robot", "captcha-delivery")):
            raise BlockedError("captcha detectado")

    @abstractmethod
    async def search(self, molecule: str) -> list[RawItem]: ...
