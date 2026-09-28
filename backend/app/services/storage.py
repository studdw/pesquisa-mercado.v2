"""
Cache (TTL) + histórico de preços.
- DATABASE_URL vazio  -> SQLite local (ok para dev; no Render free é apagado quando o serviço dorme)
- DATABASE_URL=postgres://... (Neon/Supabase gratuitos) -> persistente, recomendado em produção
"""
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from ..core.config import get_settings

_SQLITE = Path(__file__).resolve().parents[2] / "data" / "local.db"

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS cache (
        k TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS price_history (
        molecule TEXT NOT NULL, pharmacy TEXT NOT NULL, name TEXT NOT NULL,
        laboratory TEXT, price DOUBLE PRECISION, day TEXT NOT NULL,
        PRIMARY KEY (molecule, pharmacy, name, day))""",
]


class Storage:
    def __init__(self):
        self.url = get_settings().database_url
        self.pg = self.url.startswith("postgres")
        self.ph = "%s" if self.pg else "?"
        with self._conn() as c:
            cur = c.cursor()
            for s in SCHEMA:
                cur.execute(s)
            c.commit()

    def _conn(self):
        if self.pg:
            import psycopg
            return psycopg.connect(self.url, autocommit=False)
        _SQLITE.parent.mkdir(exist_ok=True)
        return sqlite3.connect(_SQLITE)

    def _exec(self, sql: str, params=(), fetch=False):
        sql = sql.replace("?", self.ph)
        with self._conn() as c:
            cur = c.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall() if fetch else None
            c.commit()
            return rows

    # ---------- cache ----------
    def get_cache(self, key: str):
        rows = self._exec("SELECT payload, created_at FROM cache WHERE k = ?", (key,), fetch=True)
        if rows and time.time() - rows[0][1] < get_settings().cache_ttl_hours * 3600:
            return json.loads(rows[0][0])
        return None

    def set_cache(self, key: str, payload) -> None:
        upsert = ("INSERT INTO cache (k, payload, created_at) VALUES (?, ?, ?) "
                  "ON CONFLICT (k) DO UPDATE SET payload = EXCLUDED.payload, created_at = EXCLUDED.created_at")
        self._exec(upsert, (key, json.dumps(payload, ensure_ascii=False), time.time()))

    # ---------- histórico ----------
    def save_history(self, products: list[dict]) -> None:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        sql = ("INSERT INTO price_history (molecule, pharmacy, name, laboratory, price, day) "
               "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (molecule, pharmacy, name, day) "
               "DO UPDATE SET price = EXCLUDED.price")
        for p in products:
            if p.get("price"):
                self._exec(sql, (p["molecule"].lower(), p["pharmacy"], p["name"], p["laboratory"], p["price"], day))

    def history(self, molecule: str) -> list[dict]:
        rows = self._exec(
            "SELECT day, pharmacy, MIN(price), AVG(price), MAX(price), COUNT(*) FROM price_history "
            "WHERE molecule = ? GROUP BY day, pharmacy ORDER BY day",
            (molecule.lower(),), fetch=True,
        )
        return [
            {"day": r[0], "pharmacy": r[1], "min": round(r[2], 2), "avg": round(r[3], 2),
             "max": round(r[4], 2), "count": r[5]}
            for r in rows or []
        ]


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = Storage()
    return _storage
