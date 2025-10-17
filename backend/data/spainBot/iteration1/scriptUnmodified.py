import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Go to the Wikipedia page for Spain
        await page.goto("https://en.wikipedia.org/wiki/Spain")

        # Locate the population value in the infobox (first td after the "Population" header)
        population_text = await page.locator(
            'xpath=//th[contains(text(),"Population")]/following-sibling::td[1]'
        ).inner_text()

        # Extract the numeric part of the population string
        import re
        match = re.search(r'[\d,]+', population_text)
        if match:
            population_number = int(match.group(0).replace(',', ''))
            print(f"The population of Spain is {population_number}")
        else:
            print("Could not find the population value.")

        await browser.close()

asyncio.run(main())