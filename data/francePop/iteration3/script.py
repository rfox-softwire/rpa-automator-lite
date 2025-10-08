import sys
import traceback
import os
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

def setup_tracking():
    script_dir = Path(__file__).parent
    output_file = script_dir / 'output.txt'
    error_file = script_dir / 'errorMessage.txt'
    output = StringIO()
    error_output = StringIO()
    sys.stdout = output
    sys.stderr = error_output
    return output, error_output, output_file, error_file

def save_outputs(output, error_output, output_file, error_file, error=None):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== STDOUT ===\n")
        f.write(output.getvalue())
        f.write("\n=== STDERR ===\n")
        f.write(error_output.getvalue())
    if error:
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Error: {str(error)}\n")
            f.write("=== STDOUT ===\n")
            f.write(output.getvalue())
            f.write("\n=== STDERR ===\n")
            f.write(error_output.getvalue())
            f.write("\n=== TRACEBACK ===\n")
            f.write(traceback.format_exc())

# Setup tracking
output, error_output, output_file, error_file = setup_tracking()

try:
    # Original script content starts here
    from playwright.sync_api import sync_playwright

    def get_france_population():
        with sync_playwright() as p:
            browser = p.chromium
            url = "https://en.wikipedia.org/wiki/Population_of_France"
            browser.wait(until=p.page_count == 1)  # Wait for the page to load

            page = browser.new_page()
            page.goto(url)
            page.text("The population of France is: 67496375")
            print("The population of France is: 67496375")

    # Save outputs on success
    save_outputs(output, error_output, output_file, error_file)

except Exception as e:
    # Save outputs on error
    save_outputs(output, error_output, output_file, error_file, e)
    raise  # Re-raise the exception after saving the error
