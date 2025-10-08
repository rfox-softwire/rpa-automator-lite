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