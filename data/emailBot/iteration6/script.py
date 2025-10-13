
import sys, os, asyncio, contextlib, atexit, traceback
from pathlib import Path
import inspect
from playwright.async_api import async_playwright, Page, Frame, Locator, ElementHandle, Browser, BrowserContext, BrowserType
from functools import wraps, lru_cache

# --- Files next to the tracked script ---
base_dir    = Path(__file__).parent
output_file = base_dir / "output.txt"
error_file  = base_dir / "errorMessage.txt"
html_file   = base_dir / "HTML.txt"
url_file    = base_dir / "url.txt"

# overwrite logs each run
sys.stdout = open(output_file, "w", encoding="utf-8")
sys.stderr = open(error_file, "w", encoding="utf-8")

# --- globals for last-seen handles ---
_LAST_PAGE = None        # type: Page | None
_LAST_BROWSER = None     # type: Browser | None
_SNAPSHOT_DONE = False
CAP_MS = 10000 

@atexit.register
def _flush_streams():
    for s in (sys.stdout, sys.stderr):
        try:
            s.flush()
            s.close()
        except Exception:
            pass

async def _save_one_page(page: "Page", idx: int | None = None):
    try:
        # skip closed pages
        if hasattr(page, "is_closed") and page.is_closed():
            return
    except Exception:
        pass

    html = await page.content()
    try:
        current_url = page.url
    except Exception:
        current_url = ""

    html_path = base_dir / f"HTML-{idx}.txt"
    url_path  = base_dir / f"url-{idx}.txt"

    html_path.write_text(html, encoding="utf-8")
    url_path.write_text(current_url, encoding="utf-8")

async def _enumerate_open_pages(anchor = None):
    pages = []
    seen = set()

    def _add(p):
        if p is None:
            return
        ident = id(p)
        if ident in seen:
            return
        seen.add(ident)
        pages.append(p)

    # 1) anchor first
    if anchor is not None:
        _add(anchor)
        try:
            ctx = anchor.context
            for p in getattr(ctx, "pages", []):
                _add(p)
            br = getattr(ctx, "browser", None)
            if br:
                for c in getattr(br, "contexts", []):
                    for p in getattr(c, "pages", []):
                        _add(p)
        except Exception:
            pass
    else:
        # 2) fall back to last page we saw
        lp = globals().get("_LAST_PAGE")
        if lp:
            return await _enumerate_open_pages(lp)

    return pages

async def _save_all_pages(anchor = None):
    pages = await _enumerate_open_pages(anchor)
    if not pages:
        return
    for i, p in enumerate(pages):
        await _save_one_page(p, idx=i+1)
    globals()["_SNAPSHOT_DONE"] = True

async def _page_from(obj):
    # direct page handle
    pg = getattr(obj, "page", None)
    if pg is not None:
        return pg
    # Locator → frame → page
    if isinstance(obj, Locator):
        try:
            fr = getattr(obj, "frame", None)
            if fr is not None:
                return getattr(fr, "page", None)
        except Exception:
            pass
    # ElementHandle → owner_frame() → page
    if isinstance(obj, ElementHandle):
        try:
            fr = await obj.owner_frame()
            if fr is not None:
                return getattr(fr, "page", None)
        except Exception:
            pass
    # Frame itself
    if isinstance(obj, Frame):
        try:
            return getattr(obj, "page", None)
        except Exception:
            pass
    # Fallback to last seen page
    return globals().get("_LAST_PAGE")

@lru_cache(maxsize=None)
def _supports_timeout(origin_cls: type, method_name: str) -> bool:
    try:
        meth = getattr(origin_cls, method_name)
        sig = inspect.signature(meth)
        return "timeout" in sig.parameters
    except (AttributeError, ValueError, TypeError):
        # Some builtins / C-accelerated callables may not expose a signature cleanly
        return False

def _cap_timeout(kwargs: dict, allow: bool):
    if not allow:
        return
    user = kwargs.get("timeout", None)
    if user is None or (isinstance(user, (int, float)) and user > CAP_MS):
        kwargs["timeout"] = CAP_MS

# --- generic async method wrapper factory ---
def _make_async_wrapper(name, origin_cls):
    orig = getattr(origin_cls, name)

    @wraps(orig)
    async def _wrapped(self, *args, **kwargs):
        if isinstance(self, Page):
            globals()["_LAST_PAGE"] = self

        # Only inject 'timeout' if the method supports it
        _cap_timeout(kwargs, _supports_timeout(origin_cls, name))

        try:
            return await orig(self, *args, **kwargs)
        except Exception as e:
            try:
                pg = await _page_from(self)
                if pg is not None:
                    await _save_all_pages(pg)
            finally:
                print(f"[tracking] {origin_cls.__name__}.{name} failed: {e}", file=sys.stderr)
            raise
    return _wrapped

# --- auto-wrap all coroutine methods on target classes (skip dangerous ones) ---
_BLACKLIST = {
    # dunders / core internals
    "__class__", "__dict__", "__getattribute__", "__init__", "__repr__", "__str__",
    "__aenter__", "__aexit__",
    # event/routing setup where side-effects/timeouts can break semantics
    "expect_event", "wait_for_event", "on", "off", "route", "unroute",
}

def _auto_wrap_async_methods(origin_cls):
    for name in dir(origin_cls):
        if name in _BLACKLIST or name.startswith("_"):
            continue
        try:
            attr = getattr(origin_cls, name)
        except Exception:
            continue
        # wrap only coroutine functions (async defs). Skip properties/descriptors.
        if inspect.iscoroutinefunction(attr):
            sentinel = f"__tracked_wrapped_{name}__"
            if getattr(origin_cls, sentinel, False):
                continue
            try:
                setattr(origin_cls, name, _make_async_wrapper(name, origin_cls))
                setattr(origin_cls, sentinel, True)
            except Exception:
                # Some C-accelerated attributes are not settable; skip gracefully
                pass

# Apply broadly
for _cls in (Page, Frame, Locator, ElementHandle, BrowserContext, Browser):
    _auto_wrap_async_methods(_cls)

# --- additionally wrap sync selector factories (parse-time errors) ---
def _wrap_sync_selector_factory(name: str):
    orig = getattr(Page, name)
    @wraps(orig)
    def _wrapped(self: "Page", *args, **kwargs):
        globals()["_LAST_PAGE"] = self
        try:
            return orig(self, *args, **kwargs)
        except Exception as e:
            # snapshot even though we're in sync context
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_save_all_pages(self))
            except RuntimeError:
                with contextlib.suppress(Exception):
                    asyncio.run(_save_all_pages(self))
            print(f"[tracking] Page.{name} failed (sync): {e}", file=sys.stderr)
            raise
    return _wrapped

for _name in ("locator", "get_by_role", "get_by_text", "get_by_label", "frame_locator"):
    if hasattr(Page, _name):
        try:
            setattr(Page, _name, _wrap_sync_selector_factory(_name))
        except Exception:
            pass


_TB_TAIL = 3  # print last 3 frames

def _format_tail_tb(exc: BaseException, tail: int) -> str:
    try:
        frames = list(traceback.walk_tb(exc.__traceback__))  # oldest → newest
        tail_frames = frames[-tail:] if tail > 0 else frames
        stack = traceback.StackSummary.extract(tail_frames)
        return "".join(stack.format())
    except Exception:
        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

def _excepthook(etype, value, tb):
    # Try to snapshot synchronously first (so it happens before the loop is closed)
    lp = globals().get("_LAST_PAGE")
    if lp is not None and not globals().get("_SNAPSHOT_DONE", False):
        try:
            asyncio.run(_save_all_pages(lp))
        except RuntimeError:
            # If a loop is currently running, schedule as a last resort
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_save_all_pages(lp))
            except Exception:
                pass

    # ... keep your concise header + tail-frames printing below ...
    try:
        print(f"Exception: {etype.__name__}: {value}", file=sys.stderr)
        print("Traceback (last 3 frame(s)):", file=sys.stderr)
        print(_format_tail_tb(value, _TB_TAIL), file=sys.stderr)
        sys.stderr.flush()
    except Exception:
        traceback.print_exception(etype, value, tb, file=sys.stderr)

sys.excepthook = _excepthook

_orig_asyncio_run = asyncio.run
def _tracked_asyncio_run(coro, *args, **kwargs):
    try:
        return _orig_asyncio_run(coro, *args, **kwargs)
    except Exception:
        lp = globals().get("_LAST_PAGE")
        if lp is not None and not globals().get("_SNAPSHOT_DONE", False):
            try:
                _orig_asyncio_run(_save_all_pages(lp))  # run on a fresh loop
            except Exception:
                pass
        raise
asyncio.run = _tracked_asyncio_run

# --- Force headed + set default timeouts; also track last browser/page ---
_orig_launch = BrowserType.launch
async def _launch_headed(self, *args, **kwargs):
    kwargs["headless"] = False
    browser: Browser = await _orig_launch(self, *args, **kwargs)
    globals()["_LAST_BROWSER"] = browser

    _orig_new_context = browser.new_context
    async def _new_context(*aa, **kk):
        ctx: BrowserContext = await _orig_new_context(*aa, **kk)
        ctx.set_default_timeout(CAP_MS)
        ctx.set_default_navigation_timeout(CAP_MS)
        return ctx
    browser.new_context = _new_context

    _orig_new_page = browser.new_page
    async def _new_page(*aa, **kk):
        page = await _orig_new_page(*aa, **kk)
        page.set_default_timeout(CAP_MS)
        page.set_default_navigation_timeout(CAP_MS)
        globals()["_LAST_PAGE"] = page
        return page
    browser.new_page = _new_page

    return browser
BrowserType.launch = _launch_headed

# --- Save-before-close wrappers ---------------------------------
_orig_page_close = Page.close
async def _tracked_page_close(self: "Page", *args, **kwargs):
    try:
        if not globals().get("_SNAPSHOT_DONE", False) and hasattr(self, "is_closed") and not self.is_closed():
            await _save_all_pages(self)
    except Exception:
        pass
    return await _orig_page_close(self, *args, **kwargs)
Page.close = _tracked_page_close

_orig_ctx_close = BrowserContext.close
async def _tracked_ctx_close(self: "BrowserContext", *args, **kwargs):
    try:
        if not globals().get("_SNAPSHOT_DONE", False):
            for pg in getattr(self, "pages", []):
                try:
                    if hasattr(pg, "is_closed") and not pg.is_closed():
                        await _save_all_pages(pg)
                        break
                except Exception:
                    pass
    except Exception:
        pass
    return await _orig_ctx_close(self, *args, **kwargs)
BrowserContext.close = _tracked_ctx_close

_orig_browser_close = Browser.close
async def _tracked_browser_close(self: "Browser", *args, **kwargs):
    try:
        if not globals().get("_SNAPSHOT_DONE", False):
            lp = globals().get("_LAST_PAGE")
            if lp is not None and hasattr(lp, "is_closed") and not lp.is_closed():
                await _save_all_pages(lp)
            else:
                for ctx in getattr(self, "contexts", []):
                    for pg in getattr(ctx, "pages", []):
                        try:
                            if hasattr(pg, "is_closed") and not pg.is_closed():
                                await _save_all_pages(pg)
                                raise StopIteration
                        except Exception:
                            pass
    except StopIteration:
        pass
    except Exception:
        pass
    return await _orig_browser_close(self, *args, **kwargs)
Browser.close = _tracked_browser_close

@atexit.register
def _snapshot_then_close():
    lp = globals().get("_LAST_PAGE")
    br = globals().get("_LAST_BROWSER")
    if lp is not None and not globals().get("_SNAPSHOT_DONE", False):
        try:
            asyncio.run(_save_all_pages(lp))
        except Exception:
            pass
    if br is not None:
        try:
            async def _do_close():
                with contextlib.suppress(Exception):
                    await br.close()
            asyncio.run(_do_close())
        except Exception:
            pass

import asyncio


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Two pages: inbox (3001) and claim‑management (3003)
        page_3001 = await context.new_page()
        page_3003 = await context.new_page()

        # 1️⃣ Open the claims inbox
        await page_3001.goto("http://localhost:3001/")

        # Ensure the Inbox view is visible
        await page_3001.wait_for_selector('a[href="#"]')
        await page_3001.click('a[href="#"]')

        # Wait for the list of message items to appear
        message_selector = ".message-item"
        await page_3001.wait_for_selector(message_selector)
        count = await page_3001.locator(message_selector).count()

        for idx in range(count):
            # 2️⃣ Open the email detail view
            await page_3001.click(f"{message_selector}:nth-child({idx + 1})")

            # Wait until the detail modal is visible
            await page_3001.wait_for_selector("div.prose", state="visible")

            # 3️⃣ Extract claim details from the opened detail view
            prose_text = await page_3001.locator("div.prose").inner_text()
            lines = [line.strip() for line in prose_text.splitlines() if line.strip()]
            data = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    data[key.strip().lower()] = value.strip()

            policy_number = data.get("policy number", "")
            description   = data.get("description", "")
            amount_str    = data.get("claim amount", "").replace("£", "").replace(",", "")
            claim_amount  = float(amount_str) if amount_str else 0.0
            date_str      = data.get("claim date", "")

            # Convert DD/MM/YYYY to YYYY-MM-DD for the <input type="date">
            day, month, year = date_str.split("/")
            iso_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            # 4️⃣ Navigate to the new‑claim form page
            await page_3003.goto("http://localhost:3003/")

            # 5️⃣ Open the New Claim modal
            await page_3003.wait_for_selector("#newClaimBtn")
            await page_3003.click("#newClaimBtn")

            # Wait for the modal to become visible
            await page_3003.wait_for_selector("form#newClaimForm", state="visible")

            # 6️⃣ Fill in the form fields (use correct IDs)
            await page_3003.fill("#policyNumber", policy_number)
            await page_3003.fill("#description", description)
            await page_3003.fill("#claimAmount", str(claim_amount))
            await page_3003.fill("#claimDate", iso_date)

            # 7️⃣ Submit the form
            await page_3003.click("button[type='submit']")

            # 8️⃣ Verify that the claim appears in the list on 3003
            await page_3003.wait_for_selector(f"text={policy_number}")

            print(f"✅ Claim {idx + 1} ({policy_number}) submitted successfully.")

            # 9️⃣ Return to the inbox for the next email
            await page_3001.goto("http://localhost:3001/")
            await page_3001.click('a[href="#"]')

        await browser.close()

asyncio.run(main())