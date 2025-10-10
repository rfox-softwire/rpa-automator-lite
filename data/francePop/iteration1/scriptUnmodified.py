import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.wikipedia.org/")
        
        # Type "France population" into the search box and submit
        search_box = page.locator('input[id="searchInput"]')
        await search_box.fill("France population")
        await search_box.press("Enter")

        # Wait for the search results to load
        await page.wait_for_load_state()

        # Extract the population from the article (using a more robust selector)
        article_locator = page.locator('a[title="France"]')  # Selects link to France article
        article_url = await article_locator.get_attribute("href")

        await page.goto(article_url)

        await page.wait_for_load_state()

        population_locator = page.locator('span[id="mw-measurement"]') # Locates span with population data
        population_text = await population_locator.inner_text()

        # Print the population
        print(f"The population of France is {population_text}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())