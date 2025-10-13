import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Two pages: inbox (3001) and new‑claim form (3003)
        page_3001 = await context.new_page()
        page_3003 = await context.new_page()

        # 1️⃣ Open the claims inbox
        await page_3001.goto("http://localhost:3001/")

        # Ensure the inbox list is visible – click the "Inbox" link if needed
        await page_3001.click('a[href="#"]')

        # Locate all message items that represent claim emails
        message_selector = ".message-item"
        await page_3001.wait_for_selector(message_selector)
        count = await page_3001.locator(message_selector).count()

        for idx in range(count):
            # 2️⃣ Click the email to open its detail view
            await page_3001.click(f"{message_selector}:nth-child({idx + 1})")

            # Wait until the detail view loads (the policy number text appears)
            await page_3001.wait_for_selector("div.prose", state="visible")

            # 3️⃣ Extract claim details from the opened detail view
            prose_text = await page_3001.locator("div.prose").inner_text()
            lines = [line.strip() for line in prose_text.splitlines() if line.strip()]
            data = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    data[key.strip().lower()] = value.strip()

            policy_number = data.get("policy number", "")
            description   = data.get("description", "")
            amount_str    = data.get("claim amount", "").replace("£", "").replace(",", "")
            claim_amount  = float(amount_str) if amount_str else 0.0
            date_str      = data.get("claim date", "")

            # 4️⃣ Navigate to the new‑claim form
            await page_3003.goto("http://localhost:3003/")

            # 5️⃣ Fill in the form fields
            await page_3003.fill("#policy-number-input", policy_number)
            await page_3003.fill("#description-input", description)
            await page_3003.fill("#claim-amount-input", str(claim_amount))
            await page_3003.fill("#claim-date-input", date_str)

            # 6️⃣ Submit the form
            await page_3003.click("button[type='submit']")

            # 7️⃣ Verify that the claim appears in the list on 3003
            await page_3003.wait_for_selector(f"text={policy_number}")

            print(f"✅ Claim {idx + 1} ({policy_number}) submitted successfully.")

            # 8️⃣ Return to the inbox for the next email
            await page_3001.goto("http://localhost:3001/")
            await page_3001.click('a[href="#"]')   # ensure inbox view

        await browser.close()

asyncio.run(main())