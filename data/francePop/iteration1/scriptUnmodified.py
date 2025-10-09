from playwright.sync_api import sync_playwright

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