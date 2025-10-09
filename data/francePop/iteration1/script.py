from playwright.sync_api import sync_playwright
from pathlib import Path
import traceback
import sys
import os
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import signal
import _thread


def main():
    # Setup output and error tracking
    output = StringIO()
    error_output = StringIO()
    sys.stdout = output
    sys.stderr = error_output
    output_file = Path(__file__).parent / "output.txt"
    error_file = Path(__file__).parent / "errorMessage.txt"
    html_file = Path(__file__).parent / "HTML.txt"
    timeout_seconds = 30

    def save_page_html(page, html_file):
        try:
            content = page.content()
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(f"Error saving HTML: {str(e)}")

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Script execution timed out after {timeout_seconds} seconds")

    # Set up timeout handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        def get_france_population():
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
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
                    browser.close()
                    return
                # Extract the population from the infobox
                try:
                    population_text = page.locator("#infobox p:nth-child(6)").inner_text()
                    population = int(population_text.split(" ")[0].replace(",", ""))
                    print(f"The population of France is {population}")
                except:
                    print("Could not find population data.")
                browser.close()
        get_france_population()
        # Save the final page HTML
        if "page" in locals() and page is not None:
            save_page_html(page, html_file)
        
        # Save output to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output.getvalue())
        
        # Save any errors
        error_content = error_output.getvalue()
        if error_content:
            with open(error_file, "w", encoding="utf-8") as f:
                f.write("=== STDERR ===\n")
                f.write(error_content)
                f.write("\n=== TRACEBACK ===\n")
                f.write(traceback.format_exc())
    
    except TimeoutError as e:
        # Handle timeout specifically
        error_msg = f"\nERROR: {str(e)}\n"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(error_msg)
        if "page" in locals() and page is not None:
            save_page_html(page, html_file)
        print(error_msg, file=sys.stderr, end="")
        sys.exit(1)
    
    except Exception as e:
        # Save any other errors
        error_msg = f"\nERROR: {str(e)}\n{traceback.format_exc()}"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write("=== ERROR ===\n")
            f.write(error_msg)
        if "page" in locals() and page is not None:
            save_page_html(page, html_file)
        print(error_msg, file=sys.stderr, end="")
        sys.exit(1)
    
    finally:
        # Ensure alarm is always disabled
        try:
            signal.alarm(0)
        except:
            pass
        
        # Restore stdout/stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        # Make sure browser is closed
        if "browser" in locals():
            try:
                browser.close()
            except:
                pass

if __name__ == "__main__":
    main()
