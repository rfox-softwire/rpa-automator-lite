from playwright.sync_api import sync_playwright
from pathlib import Path
import traceback
import sys
import os
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import threading
from queue import Queue
import time
import ctypes


def main():
    # Debug information
    print("Script started")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script location: {__file__}")

    # Setup output and error tracking
    output = StringIO()
    error_output = StringIO()
    sys.stdout = output
    sys.stderr = error_output
    output_file = Path(__file__).parent / "output.txt"
    error_file = Path(__file__).parent / "errorMessage.txt"
    html_file = Path(__file__).parent / "HTML.txt"
    timeout_seconds = 10
    page = None  # Initialize page variable
    browser = None  # Initialize browser variable
    playwright = None  # Initialize playwright instance

    def save_page_html(page, html_file):
        try:
            if page and not page.is_closed():
                content = page.content()
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception as e:
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(f"Error saving HTML: {str(e)}")

    def save_outputs():
        try:
            # Ensure directory exists
            output_dir = Path(__file__).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save standard output
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output.getvalue())
            
            # Save errors if any
            error_content = error_output.getvalue()
            if error_content:
                with open(error_file, "w", encoding="utf-8") as f:
                    f.write("=== STDERR ===\n")
                    f.write(error_content)
                    f.write("\n=== TRACEBACK ===\n")
                    f.write(traceback.format_exc())
        except Exception as e:
            print(f"Error saving outputs: {str(e)}", file=sys.stderr)

    timed_out = False

    def timeout_handler():
        nonlocal timed_out
        timed_out = True
        # Raise an exception to break out of any ongoing operations
        raise TimeoutError("Script execution timed out")

    # Set up timer for Windows
    timer = threading.Timer(timeout_seconds, timeout_handler)
    timer.daemon = True
    timer.start()

    try:
        # Initialize Playwright and browser
        print("Initializing Playwright...")
        playwright = sync_playwright().start()
        print("Launching browser...")
        browser = playwright.chromium.launch(headless=False)
        print("Creating new page...")
        page = browser.new_page()
        script_content = []
        in_function = False
        def get_france_population():
            page.goto("https://www.wikipedia.org/")
            # Search for France
            page.locator("#searchInput").fill("France")
            page.locator("#searchButton").click()
            page.wait_for_load_state("networkidle")
            # Navigate to the France article
            try:
                page.locator('//a[contains(text(), "France")]').click()
                page.wait_for_load_state("networkidle")
            except:
                print("Could not find France article link.")
                return
            # Extract the population from the infobox
            try:
                population_text = page.locator("#infobox p:nth-child(6)").inner_text()
                population = int(population_text.split(" ")[0].replace(",", ""))
                print(f"The population of France is {population}")
            except:
                print("Could not find population data.")
        get_france_population()
    except TimeoutError as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
    except Exception as e:
        if not timed_out:  # Only handle if not a timeout
            error_msg = f"\nERROR: {str(e)}\n{traceback.format_exc()}"
            print(error_msg, file=sys.stderr)
    
    # Always try to save HTML if we have a page
    try:
        if page is not None and not page.is_closed():
            save_page_html(page, html_file)
    except Exception as e:
        error_msg = f"Error saving page HTML: {str(e)}\n"
        error_output.write(error_msg)
    
    # Save outputs (including any error messages)
    try:
        save_outputs()
    except Exception as e:
        print(f"Error saving outputs: {str(e)}", file=sys.stderr)
    
    # Cleanup resources
    try:
        timer.cancel()  # Cancel the timer if it's still running
    except:
        pass
        
    if browser is not None:
        try:
            browser.close()
        except:
            pass
    if playwright is not None:
        try:
            playwright.stop()
        except:
            pass
    
    # Restore stdout/stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    
    # Exit with error if we timed out
    if timed_out:
        sys.exit(1)

if __name__ == "__main__":
    main()
