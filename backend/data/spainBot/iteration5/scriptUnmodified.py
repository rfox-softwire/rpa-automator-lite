import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Go to the Wikipedia page for Spain
        await page.goto("https://en.wikipedia.org/wiki/Spain")

        # Locate the first <th> that contains the text "Population" in the infobox header
        population_header = page.locator('//th[contains(@class,"infobox-header") and contains(., "Population")]')
        # Get the following sibling <td> which holds the population value
        population_text = await (
            population_header
            .locator('following-sibling::tr[1]//td')
            .inner_text()
        )

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