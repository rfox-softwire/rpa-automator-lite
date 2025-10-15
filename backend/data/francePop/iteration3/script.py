
import sys, os, asyncio, contextlib, atexit, traceback
from pathlib import Path
from playwright.async_api import async_playwright, Page, Locator, ElementHandle, BrowserType, Browser, BrowserContext

# --- Files next to the tracked script ---
base_dir    = Path(__file__).parent
output_file = base_dir / "output.txt"
error_file  = base_dir / "errorMessage.txt"
html_file   = base_dir / "HTML.txt"

# overwrite logs each run
sys.stdout = open(output_file, "w", encoding="utf-8")
sys.stderr = open(error_file, "w", encoding="utf-8")

# --- globals for last-seen handles ---
_LAST_PAGE = None        # type: Page | None
_LAST_BROWSER = None     # type: Browser | None

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

# ---- Tail-only traceback for errorMessage.txt (fixed to last 8 frames) ----
_TB_TAIL = 8  # fixed tail length

def _format_tail_tb(exc: BaseException, tail: int) -> str:
    try:
        frames = list(traceback.walk_tb(exc.__traceback__))  # oldest -> newest
        tail_frames = frames[-tail:] if tail > 0 else frames
        stack = traceback.StackSummary.extract(tail_frames)
        return "".join(stack.format())
    except Exception:
        # Fallback to full traceback if anything goes wrong
        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

def _excepthook(etype, value, tb):
    lp = globals().get("_LAST_PAGE")
    if lp is not None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_save_html(lp))
        except RuntimeError:
            with contextlib.suppress(Exception):
                asyncio.run(_save_html(lp))
    # concise header with full Playwright message (includes Call log), then tail frames only
    try:
        print(f"Exception: {etype.__name__}: {value}", file=sys.stderr)
        # print("Traceback (last 8 frame(s)):", file=sys.stderr)
        # print(_format_tail_tb(value, _TB_TAIL), file=sys.stderr)
        sys.stderr.flush()
    except Exception:
        traceback.print_exception(etype, value, tb, file=sys.stderr)

sys.excepthook = _excepthook

def _wrap_page_method(name: str):
    orig = getattr(Page, name)
    async def wrapper(self: "Page", *args, **kwargs):
        globals()["_LAST_PAGE"] = self
        # enforce a max timeout in ms (cap), but keep it Playwright-native
        cap_ms = 10000  # your timeout_seconds * 1000
        user_ms = kwargs.get("timeout", None)
        if user_ms is None or user_ms > cap_ms:
            kwargs["timeout"] = cap_ms
        try:
            return await orig(self, *args, **kwargs)   # <-- no asyncio.wait_for
        except Exception as e:
            await _save_html(self)
            print(f"[tracking] Page.{name} failed: {e}", file=sys.stderr)
            raise
    return wrapper

def _wrap_locator_method(name: str):
    orig = getattr(Locator, name)
    async def wrapper(self: "Locator", *args, **kwargs):
        # find a Page for snapshot
        page = None
        try:
            page = getattr(self, "page", None) or getattr(getattr(self, "frame", None), "page", None)
        except Exception:
            page = None
        if page is None:
            page = globals().get("_LAST_PAGE")

        cap_ms = 10000  # your timeout_seconds * 1000
        user_ms = kwargs.get("timeout", None)
        if user_ms is None or user_ms > cap_ms:
            kwargs["timeout"] = cap_ms
        try:
            return await orig(self, *args, **kwargs)   # <-- no asyncio.wait_for
        except Exception as e:
            if page is not None:
                await _save_html(page)
            print(f"[tracking] Locator.{name} failed: {e}", file=sys.stderr)
            raise
    return wrapper

def _wrap_page_sync_method(name: str):
    orig = getattr(Page, name)
    def wrapper(self: "Page", *args, **kwargs):
        globals()["_LAST_PAGE"] = self
        try:
            return orig(self, *args, **kwargs)
        except Exception as e:
            # try to save HTML even though we're in sync code
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_save_html(self))  # schedule on current loop
            except RuntimeError:
                with contextlib.suppress(Exception):
                    asyncio.run(_save_html(self))     # last resort if no loop
            try:
                print(f"Exception in Page.{name}: {e}", file=sys.stderr)
                sys.stderr.flush()
            except Exception:
                pass
            raise
    return wrapper

def _wrap_element_method(name: str):
    orig = getattr(ElementHandle, name)
    async def wrapper(self: "ElementHandle", *args, **kwargs):
        # best-effort page
        page = None
        try:
            page = getattr(getattr(self, "frame", None), "page", None)
        except Exception:
            page = None
        if page is None:
            page = globals().get("_LAST_PAGE")

        cap_ms = 10000  # your timeout_seconds * 1000
        user_ms = kwargs.get("timeout", None)
        if user_ms is None or user_ms > cap_ms:
            kwargs["timeout"] = cap_ms
        try:
            return await orig(self, *args, **kwargs)   # <-- no asyncio.wait_for
        except Exception as e:
            if page is not None:
                await _save_html(page)
            print(f"[tracking] ElementHandle.{name} failed: {e}", file=sys.stderr)
            raise
    return wrapper


# --- Install wrappers once ---
if not getattr(Page, "__tracked_patched__", False):
    # Page methods (high-impact)
    for _name in (
        "goto",
        "wait_for_load_state",
        "wait_for_selector",
        "wait_for_url",
        "click",
        "query_selector",
        "inner_text",
        "text_content",
    ):
        if hasattr(Page, _name):
            setattr(Page, _name, _wrap_page_method(_name))
    
    # Locator methods (common pain points)
    for _lname in ("wait_for", "click", "inner_text", "text_content", "get_attribute"):
        if hasattr(Locator, _lname):
            setattr(Locator, _lname, _wrap_locator_method(_lname))

    # NEW: wrap sync selector factories (parse-time failures)
    if hasattr(Page, "locator"):
        Page.locator = _wrap_page_sync_method("locator")
    if hasattr(Page, "get_by_role"):
        Page.get_by_role = _wrap_page_sync_method("get_by_role")
    if hasattr(Page, "get_by_text"):
        Page.get_by_text = _wrap_page_sync_method("get_by_text")

    # NEW: ElementHandle method wrappers (query_selector returns ElementHandle)
    for _ename in ("inner_text", "text_content"):
        if hasattr(ElementHandle, _ename):
            setattr(ElementHandle, _ename, _wrap_element_method(_ename))

    Page.__tracked_patched__ = True

# --- Force headed + set default timeouts; also track last browser/page ---
_orig_launch = BrowserType.launch
async def _launch_headed(self, *args, **kwargs):
    kwargs["headless"] = False
    browser: Browser = await _orig_launch(self, *args, **kwargs)
    globals()["_LAST_BROWSER"] = browser

    _orig_new_context = browser.new_context
    async def _new_context(*aa, **kk):
        ctx: BrowserContext = await _orig_new_context(*aa, **kk)
        ctx.set_default_timeout(10000)
        ctx.set_default_navigation_timeout(10000)
        return ctx
    browser.new_context = _new_context

    _orig_new_page = browser.new_page
    async def _new_page(*aa, **kk):
        page = await _orig_new_page(*aa, **kk)
        page.set_default_timeout(10000)
        page.set_default_navigation_timeout(10000)
        globals()["_LAST_PAGE"] = page
        return page
    browser.new_page = _new_page

    return browser
BrowserType.launch = _launch_headed

@atexit.register
def _final_snapshot_if_missing():
    lp = globals().get("_LAST_PAGE")
    if lp is not None and not html_file.exists():
        try:
            asyncio.run(_save_html(lp))
        except Exception:
            pass

@atexit.register
def _close_browser_if_any():
    br = globals().get("_LAST_BROWSER")
    if br is None:
        return
    try:
        # Best-effort async close after user code finishes
        async def _do_close():
            with contextlib.suppress(Exception):
                await br.close()
        asyncio.run(_do_close())
    except Exception:
        pass

import asyncio


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Open the France article and wait for the content to load completely
        await page.goto("https://en.wikipedia.org/wiki/France", wait_until="domcontentloaded")

        # Increase timeout to give Wikipedia time to render the infobox
        population_selector = (
            "//table[contains(@class,'infobox')]"
            "//tr[th[contains(text(),'Population')]]/td[1]"
        )
        element = await page.wait_for_selector(population_selector, state="visible", timeout=60000)
        population_text = await element.inner_text()

        # Keep only digits and commas, then remove commas
        cleaned_population = "".join(
            ch for ch in population_text if ch.isdigit() or ch == ","
        ).replace(",", "")

        print(f"The population of France is {cleaned_population}")

        await browser.close()

asyncio.run(main())