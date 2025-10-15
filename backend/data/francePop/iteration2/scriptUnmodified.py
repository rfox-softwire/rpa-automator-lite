import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to the France Wikipedia article and wait for full load
        await page.goto("https://en.wikipedia.org/wiki/France", wait_until="load")

        # Locate the population value in the infobox (first td of the Population row)
        population_selector = (
            "//table[contains(@class,'infobox')]"
            "//tr[th[contains(text(),'Population')]]/td[1]"
        )
        element = await page.wait_for_selector(population_selector, state="visible")
        population_text = await element.inner_text()

        # Clean the extracted text: keep digits and commas, then remove commas
        cleaned_population = "".join(
            ch for ch in population_text if ch.isdigit() or ch == ","
        ).replace(",", "")

        print(f"The population of France is {cleaned_population}")

        await browser.close()

asyncio.run(main())