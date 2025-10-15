import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Go directly to the France article on Wikipedia
        await page.goto("https://en.wikipedia.org/wiki/France")

        # Locate the population row in the infobox and extract its value
        population_selector = (
            "table.infobox tr:has(td:has-text('Population')) td:nth-child(2)"
        )
        element = await page.wait_for_selector(population_selector)
        population_text = await element.inner_text()

        # Clean up the extracted text (remove commas, footnotes, etc.)
        cleaned_population = "".join(
            ch for ch in population_text if ch.isdigit() or ch == ","
        ).replace(",", "")

        print(f"The population of France is {cleaned_population}")

        await browser.close()

asyncio.run(main())