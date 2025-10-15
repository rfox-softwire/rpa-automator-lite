
import sys, os, asyncio, contextlib, atexit, traceback
from pathlib import Path
import inspect
from playwright.async_api import async_playwright, Page, Frame, Locator, ElementHandle, Browser, BrowserContext, BrowserType
from functools import wraps, lru_cache

base_directory = Path(__file__).parent
output_file = base_directory / "output.txt"
error_file = base_directory / "errorMessage.txt"

sys.stdout = open(output_file, "w", encoding="utf-8")
sys.stderr = open(error_file, "w", encoding="utf-8")

LAST_PAGE = None
LAST_BROWSER = None
SNAPSHOT_DONE = False
DEFAULT_TIMEOUT = 10000 
MAX_TRACEBACK_LENGTH = 3
EXCLUDED_ATTRIBUTES = ('expect_event', 'wait_for_event', 'on', 'off', 'route', 'unroute')

async def save_one_page(page, page_index):
    if page.is_closed():
        return

    html = await page.content()
    current_url = getattr(page, "url", "")

    html_path = base_directory / f"HTML-{page_index}.txt"
    url_path = base_directory / f"url-{page_index}.txt"

    html_path.write_text(html, encoding="utf-8")
    url_path.write_text(current_url, encoding="utf-8")

async def get_open_pages(first_page):
    pages = []
    seen = set()

    def add_page(page):
        page_id = id(page)
        if page_id in seen:
            return
        seen.add(page_id)
        pages.append(page)

    if first_page is not None:
        add_page(first_page)
        try:
            first_page_context = first_page.context
            for page in getattr(first_page_context, "pages", []):
                add_page(page)
            browser = getattr(first_page_context, "browser", None)
            if browser:
                for browser_context in getattr(browser, "contexts", []):
                    for page in getattr(browser_context, "pages", []):
                        add_page(page)
        except Exception:
            pass
    else:
        if LAST_PAGE:
            return await get_open_pages(LAST_PAGE)

    return pages

async def save_all_pages(first_page):
    pages = await get_open_pages(first_page)
    if not pages:
        return
    for index, page in enumerate(pages):
        await save_one_page(page, page_index=index+1)
    globals()["SNAPSHOT_DONE"] = True

async def get_page_from_playwright_element(playwright_element):
    page = getattr(playwright_element, "page", None)
    if page is not None:
        return page
    if isinstance(playwright_element, Locator):
        try:
            frame = getattr(playwright_element, "frame", None)
            if frame is not None:
                return getattr(frame, "page", None)
        except Exception:
            pass
    if isinstance(playwright_element, ElementHandle):
        try:
            frame = await playwright_element.owner_frame()
            if frame is not None:
                return getattr(frame, "page", None)
        except Exception:
            pass
    if isinstance(playwright_element, Frame):
        try:
            return getattr(playwright_element, "page", None)
        except Exception:
            pass
    return LAST_PAGE

@lru_cache(maxsize=None)
def check_class_supports_timeout(playwright_class, method_name):
    try:
        method = getattr(playwright_class, method_name)
        signature = inspect.signature(method)
        return "timeout" in signature.parameters
    except (AttributeError, ValueError, TypeError):
        return False

def limit_timeout_value(keyword_arguments, allow):
    if not allow:
        return
    timeout = keyword_arguments.get("timeout", None)
    if timeout is None or (isinstance(timeout, (int, float)) and timeout > DEFAULT_TIMEOUT):
        keyword_arguments["timeout"] = DEFAULT_TIMEOUT

def create_async_method_wrapper(method_name, playwright_class):
    method = getattr(playwright_class, method_name)

    @wraps(method)
    async def wrapper_function(self, *args, **kwargs):
        if isinstance(self, Page):
            globals()["LAST_PAGE"] = self

        supports_timeout = check_class_supports_timeout(playwright_class, method_name)
        limit_timeout_value(kwargs, supports_timeout)

        try:
            return await method(self, *args, **kwargs)
        except Exception as error:
            try:
                page = await get_page_from_playwright_element(self)
                await save_all_pages(page)
            finally:
                print(f"[tracking] {playwright_class.__name__}.{method_name} failed: {error}", file=sys.stderr)
            raise
    
    return wrapper_function

def wrap_async_methods(playwright_class):
    for name in dir(playwright_class):
        if name in EXCLUDED_ATTRIBUTES or name.startswith("_"):
            continue
        try:
            method = getattr(playwright_class, name)
        except Exception:
            continue
        if inspect.iscoroutinefunction(method):
            tracker_added = f"__tracker_wrapped_{name}__"
            if getattr(playwright_class, tracker_added, False):
                continue
            try:
                setattr(playwright_class, name, create_async_method_wrapper(name, playwright_class))
                setattr(playwright_class, tracker_added, True)
            except Exception:
                pass

for playwright_class in (Page, Frame, Locator, ElementHandle, BrowserContext, Browser):
    wrap_async_methods(playwright_class)

def create_sync_selector_wrapper(method_name):
    method = getattr(Page, method_name)
    @wraps(method)
    def wrapper_function(self, *args, **kwargs):
        globals()["LAST_PAGE"] = self
        try:
            return method(self, *args, **kwargs)
        except Exception as error:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(save_all_pages(self))
            except RuntimeError:
                with contextlib.suppress(Exception):
                    asyncio.run(save_all_pages(self))
            print(f"[tracking] Page.{method_name} failed (sync): {error}", file=sys.stderr)
            raise
    return wrapper_function

for method_name in ("locator", "get_by_role", "get_by_text", "get_by_label", "frame_locator"):
    if hasattr(Page, method_name):
        try:
            setattr(Page, method_name, create_sync_selector_wrapper(method_name))
        except Exception:
            pass

def format_traceback(exception, traceback_tail):
    try:
        frames = list(traceback.walk_tb(exception.__traceback__)) 
        tail_frames = frames[-traceback_tail:] if traceback_tail > 0 else frames
        stack = traceback.StackSummary.extract(tail_frames)
        return "".join(stack.format())
    except Exception:
        return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

def exception_hook(exception_type, exception_value, exception_traceback):
    if LAST_PAGE is not None and not SNAPSHOT_DONE:
        try:
            asyncio.run(save_all_pages(LAST_PAGE))
        except RuntimeError:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(save_all_pages(LAST_PAGE))
            except Exception:
                pass

    try:
        print(f"Exception: {exception_type.__name__}: {exception_value}", file=sys.stderr)
        print("Traceback (last {MAX_TRACEBACK_LENGTH} frame(s)):", file=sys.stderr)
        print(format_traceback(exception_value, MAX_TRACEBACK_LENGTH), file=sys.stderr)
        sys.stderr.flush()
    except Exception:
        traceback.print_exception(exception_type, exception_value, exception_traceback, file=sys.stderr)

sys.excepthook = exception_hook

asyncio_run_reference = asyncio.run
def asyncio_run_tracking(coroutine, *args, **kwargs):
    try:
        return asyncio_run_reference(coroutine, *args, **kwargs)
    except Exception:
        if LAST_PAGE is not None and not SNAPSHOT_DONE:
            try:
                asyncio_run_reference(save_all_pages(LAST_PAGE))
            except Exception:
                pass
        raise
asyncio.run = asyncio_run_tracking

browser_launch_reference = BrowserType.launch
async def launch_playwright_headed(self, *args, **kwargs):
    kwargs["headless"] = False
    browser = await browser_launch_reference(self, *args, **kwargs)
    globals()["LAST_BROWSER"] = browser

    new_context_reference = browser.new_context
    async def new_context(*args, **kwargs):
        context = await new_context_reference(*args, **kwargs)
        context.set_default_timeout(DEFAULT_TIMEOUT)
        context.set_default_navigation_timeout(DEFAULT_TIMEOUT)
        return context
    browser.new_context = new_context

    new_page_reference = browser.new_page
    async def new_page(*args, **kwargs):
        page = await new_page_reference(*args, **kwargs)
        page.set_default_timeout(DEFAULT_TIMEOUT)
        page.set_default_navigation_timeout(DEFAULT_TIMEOUT)
        globals()["LAST_PAGE"] = page
        return page
    browser.new_page = new_page

    return browser
BrowserType.launch = launch_playwright_headed

page_close_reference = Page.close
async def page_close_tracking(self, *args, **kwargs):
    try:
        if not SNAPSHOT_DONE and hasattr(self, "is_closed") and not self.is_closed():
            await save_all_pages(self)
    except Exception:
        pass
    return await page_close_reference(self, *args, **kwargs)
Page.close = page_close_tracking

context_close_reference = BrowserContext.close
async def context_close_tracking(self, *args, **kwargs):
    try:
        if not SNAPSHOT_DONE:
            for page in getattr(self, "pages", []):
                try:
                    if hasattr(page, "is_closed") and not page.is_closed():
                        await save_all_pages(page)
                        break
                except Exception:
                    pass
    except Exception:
        pass
    return await context_close_reference(self, *args, **kwargs)
BrowserContext.close = context_close_tracking

browser_close_reference = Browser.close
async def browser_close_tracking(self, *args, **kwargs):
    try:
        if not SNAPSHOT_DONE:
            if LAST_PAGE and hasattr(LAST_PAGE, "is_closed") and not LAST_PAGE.is_closed():
                await save_all_pages(LAST_PAGE)
            else:
                for context in getattr(self, "contexts", []):
                    for page in getattr(context, "pages", []):
                        try:
                            if hasattr(page, "is_closed") and not page.is_closed():
                                await save_all_pages(page)
                                raise StopIteration
                        except Exception:
                            pass
    except StopIteration:
        pass
    except Exception:
        pass
    return await browser_close_reference(self, *args, **kwargs)
Browser.close = browser_close_tracking

@atexit.register
def flush_streams_on_exit():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
            stream.close()
        except Exception:
            pass

@atexit.register
def snapshot_then_close_on_exit():
    if LAST_PAGE and not SNAPSHOT_DONE:
        try:
            asyncio.run(save_all_pages(LAST_PAGE))
        except Exception:
            pass
    if LAST_BROWSER:
        try:
            async def close_browser():
                with contextlib.suppress(Exception):
                    await LAST_BROWSER.close()
            asyncio.run(close_browser())
        except Exception:
            pass

import asyncio
from datetime import datetime


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

            # Convert the date to yyyy-mm-dd format for <input type="date">
            try:
                claim_date_iso = datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                claim_date_iso = ""

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
            if claim_date_iso:
                await page_3003.fill("#claimDate", claim_date_iso)

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