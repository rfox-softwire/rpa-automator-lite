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
        f.write("=== STDOUT ===")
        f.write(output.getvalue())
        f.write("=== STDERR ===")
        f.write(error_output.getvalue())
    
    if error:
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Error: {str(error)}")
            f.write("=== STDOUT ===")
            f.write(output.getvalue())
            f.write("=== STDERR ===")
            f.write(error_output.getvalue())
            f.write("=== TRACEBACK ===")
            f.write(traceback.format_exc())

output, error_output, output_file, error_file = setup_tracking()


from playwright.sync_api import sync_playwright

def get_france_population():
    """
    Retrieves the population of France using Wikipedia and prints it to the console.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()  # Or any browser you prefer
        url = "https://en.wikipedia.org/wiki/Population_of_France"
        page = browser.new_page()
        page.goto(url)
        population_element = page.locator("#population")
        try:
            population_text = population_element.get_text()
            print(f"The population of France is: {population_text}")
        except Exception as e:
            print(f"An error occurred while retrieving the population: {e}")

if __name__ == '__main__':
    get_france_population()

if __name__ == "__main__":
    try:
        # Call the original script's main function if it exists
        if 'main' in locals() and callable(main):
            main()
        save_outputs(output, error_output, output_file, error_file)
    except Exception as e:
        save_outputs(output, error_output, output_file, error_file, e)
        raise  # Re-raise the exception after saving the error
