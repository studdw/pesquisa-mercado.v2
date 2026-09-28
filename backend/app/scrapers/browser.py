"""Playwright com stealth — usado só como fallback (consome ~300MB de RAM)."""
import asyncio
import random

_browser = None
_pw = None
_sem = asyncio.Semaphore(1)  # 1 aba por vez: cabe nos 512MB do Render free


async def _get_browser():
    global _browser, _pw
    if _browser is None or not _browser.is_connected():
        from playwright.async_api import async_playwright
        _pw = await async_playwright().start()
        _browser = await _pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                  "--disable-blink-features=AutomationControlled"],
        )
    return _browser


async def fetch_rendered(url: str, timeout_ms: int = 25000) -> str:
    async with _sem:
        browser = await _get_browser()
        ctx = await browser.new_context(locale="pt-BR", viewport={"width": 1366, "height": 850})
        page = await ctx.new_page()
        try:
            try:
                from playwright_stealth import stealth_async
                await stealth_async(page)
            except ImportError:
                pass
            # bloqueia imagens/fontes: mais rápido e menos memória
            await page.route("**/*.{png,jpg,jpeg,webp,gif,svg,woff,woff2}", lambda r: r.abort())
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_timeout(random.randint(1500, 3000))
            await page.mouse.wheel(0, 1200)
            await page.wait_for_timeout(800)
            return await page.content()
        finally:
            await ctx.close()


async def shutdown():
    global _browser, _pw
    if _browser:
        await _browser.close()
    if _pw:
        await _pw.stop()
    _browser = _pw = None
