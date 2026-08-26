import asyncio
from playwright.async_api import async_playwright

async def get_m3u8_link():
    async with async_playwright() as p:
        # হেডলেস ব্রাউজার চালু করা (গিটহাব অ্যাকশনসের জন্য headless=True জরুরি)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        m3u8_url = None

        # নেটওয়ার্ক রিকোয়েস্ট ট্র্যাক করার জন্য ইভেন্ট লিসেনার
        def handle_request(request):
            nonlocal m3u8_url
            if ".m3u8" in request.url:
                m3u8_url = request.url

        page.on("request", handle_request)

        try:
            print("Opening target page...")
            # আপনার টার্গেট লিংক
            await page.goto("https://crichdsee.st/player.php?id=willow", timeout=60000)
            
            # প্লেয়ার লোড হওয়ার জন্য ১৫-২০ সেকেন্ড অপেক্ষা করা (স্ক্রিনশটের মেসেজ অনুযায়ী)
            print("Waiting for player to load and fetch stream...")
            await asyncio.sleep(20)

        except Exception as e:
            print(f"Error occurred: {e}")

        await browser.close()

        if m3u8_url:
            print(f"Found M3U8 Link: {m3u8_url}")
            # লিংকটি একটি টেক্সট ফাইলে সেভ করে রাখা
            with open("stream.txt", "w") as f:
                f.write(m3u8_url)
        else:
            print("M3U8 link not found!")

if __name__ == "__main__":
    asyncio.run(get_m3u8_link())
      
