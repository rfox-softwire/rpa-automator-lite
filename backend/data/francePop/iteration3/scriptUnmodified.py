import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Open the France article and wait for the content to load completely
        await page.goto("https://en.wikipedia.org/wiki/France", wait_until="domcontentloaded")

        # Increase timeout to give Wikipedia time to render the infobox
        population_selector = (
            "//table[contains(@class,'infobox')]"
            "//tr[th[contains(text(),'Population')]]/td[1]"
        )
        element = await page.wait_for_selector(population_selector, state="visible", timeout=60000)
        population_text = await element.inner_text()

        # Keep only digits and commas, then remove commas
        cleaned_population = "".join(
            ch for ch in population_text if ch.isdigit() or ch == ","
        ).replace(",", "")

        print(f"The population of France is {cleaned_population}")

        await browser.close()

asyncio.run(main())