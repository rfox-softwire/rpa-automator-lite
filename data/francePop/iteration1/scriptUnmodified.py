from playwright.async_api import async_playwright

async def main():
    url = "https://www.wikipedia.org/"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.locator("text=Search Wikipedia").click()
        await page.locator("#searchInput").fill("France")
        await page.locator("#searchButton").click()
        await page.locator("h2:has-text('Demographics')").click()
        population_locator = page.locator("//div[@id='Population']//span[contains(.,'people')]")

        try:
            population_text = await population_locator.inner_text()
            population = int(population_text.split(" ")[0].replace(",", ""))
            print(f"The population of France is {population}")
        except AttributeError:
            print("Could not find the population.")
        finally:
            await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())