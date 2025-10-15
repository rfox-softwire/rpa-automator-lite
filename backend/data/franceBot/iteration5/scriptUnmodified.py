import asyncio
from playwright.async_api import async_playwright
import re

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Open Wikipedia homepage
        await page.goto("https://www.wikipedia.org/", wait_until="load")

        # 2. Search for "France"
        await page.fill("#searchInput", "France")
        await page.press("#searchInput", "Enter")

        # 3. Wait until the article title is visible (ensures we are on the France page)
        await page.wait_for_selector("h1#firstHeading", timeout=15000)

        # 4. Locate the population value in the infobox
        #    The population is usually inside a <tr> whose <th> contains "Population".
        #    We grab the first <td> that follows that <th>.
        population_locator = page.locator(
            "//table[contains(@class,'infobox')]"
            "//tr[th[contains(.,'Population')]]/td[1]"
        )
        await population_locator.wait_for(state="visible", timeout=15000)

        # 5. Extract and clean the text
        raw_text = await population_locator.inner_text()
        cleaned_text = re.sub(r"\[\d+\]", "", raw_text).strip()

        print(f"The population of France is {cleaned_text}")

        await browser.close()

asyncio.run(main())