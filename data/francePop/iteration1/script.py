
import sys, os, asyncio, contextlib, atexit
from pathlib import Path
from playwright.async_api import async_playwright, Page, Locator, BrowserType, Browser, BrowserContext, TimeoutError as PWTimeoutError

# --- Files next to the tracked script ---
base_dir    = Path(__file__).parent
output_file = base_dir / "output.txt"
error_file  = base_dir / "errorMessage.txt"
html_file   = base_dir / "HTML.txt"

# overwrite logs each run
sys.stdout = open(output_file, "w", encoding="utf-8")
sys.stderr = open(error_file, "w", encoding="utf-8")

@atexit.register
def _flush_streams():
    for s in (sys.stdout, sys.stderr):
        try:
            s.flush()
            s.close()
        except Exception:
            pass

async def _save_html(page: "Page"):
    try:
        html = await page.content()
        html_file.write_text(html, encoding="utf-8")
    except Exception as e:
        print(f"[tracking] Failed to save HTML: {e!r}", file=sys.stderr)

def _wrap_page_method(name: str):
    orig = getattr(Page, name)
    async def wrapper(self: "Page", *args, **kwargs):
        timeout_s = 10
        try:
            return await asyncio.wait_for(orig(self, *args, **kwargs), timeout=timeout_s)
        except (asyncio.TimeoutError, PWTimeoutError):
            await _save_html(self)
            raise
    return wrapper

def _wrap_locator_method(name: str):
    orig = getattr(Locator, name)
    async def wrapper(self: "Locator", *args, **kwargs):
        timeout_s = 10
        # best-effort to find page for snapshot
        page = None
        try:
            page = getattr(self, "page", None)
        except Exception:
            page = None
        try:
            return await asyncio.wait_for(orig(self, *args, **kwargs), timeout=timeout_s)
        except (asyncio.TimeoutError, PWTimeoutError):
            if page is not None:
                await _save_html(page)
            else:
                print("[tracking] Timeout on Locator but no page reference; HTML not saved.", file=sys.stderr)
            raise
    return wrapper

# --- Install wrappers once ---
if not getattr(Page, "__tracked_patched__", False):
    # Page methods (high-impact)
    if hasattr(Page, "goto"):
        Page.goto = _wrap_page_method("goto")
    if hasattr(Page, "wait_for_load_state"):
        Page.wait_for_load_state = _wrap_page_method("wait_for_load_state")
    if hasattr(Page, "wait_for_selector"):
        Page.wait_for_selector = _wrap_page_method("wait_for_selector")
    if hasattr(Page, "wait_for_url"):
        Page.wait_for_url = _wrap_page_method("wait_for_url")
    if hasattr(Page, "click"):
        Page.click = _wrap_page_method("click")

    # Locator methods (add the two common reads)
    if hasattr(Locator, "wait_for"):
        Locator.wait_for = _wrap_locator_method("wait_for")
    if hasattr(Locator, "click"):
        Locator.click = _wrap_locator_method("click")
    if hasattr(Locator, "inner_text"):
        Locator.inner_text = _wrap_locator_method("inner_text")
    if hasattr(Locator, "text_content"):
        Locator.text_content = _wrap_locator_method("text_content")

    Page.__tracked_patched__ = True

# --- Force headed by default ---
_orig_launch = BrowserType.launch
async def _launch_headed(self, *args, **kwargs):
    kwargs["headless"] = False
    browser: Browser = await _orig_launch(self, *args, **kwargs)

    # ensure every context/page inherits your timeout as default
    _orig_new_context = browser.new_context
    async def _new_context(*aa, **kk):
        ctx: BrowserContext = await _orig_new_context(*aa, **kk)
        ctx.set_default_timeout(10000)
        ctx.set_default_navigation_timeout(10000)
        return ctx
    browser.new_context = _new_context

    # when scripts call browser.new_page() directly (like your sample), set page defaults
    _orig_new_page = browser.new_page
    async def _new_page(*aa, **kk):
        page = await _orig_new_page(*aa, **kk)
        page.set_default_timeout(10000)
        page.set_default_navigation_timeout(10000)
        return page
    browser.new_page = _new_page

    return browser
BrowserType.launch = _launch_headed



async def main():
    url = "https://www.wikipedia.org/"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.locator("text=Search Wikipedia").click()
        await page.locator("#searchInput").fill("France")
        await page.locator("#searchButton").click()
        await page.locator("h2:has-text('Demographics')").click()
        population_locator = page.locator("//div[@id='Population']//span[contains(.,'people')]")

        try:
            population_text = await population_locator.inner_text()
            population = int(population_text.split(" ")[0].replace(",", ""))
            print(f"The population of France is {population}")
        except AttributeError:
            print("Could not find the population.")
        finally:
            await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())