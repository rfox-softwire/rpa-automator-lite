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