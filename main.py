import asyncio
from playwright.async_api import async_playwright

async def get_m3u8_link():
    async with async_playwright() as p:
        # হেডলেস ব্রাউজার চালু করা
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        m3u8_url = None
        referer_url = ""

        # নেটওয়ার্ক রিকোয়েস্ট ট্র্যাক করার জন্য ইভেন্ট লিসেনার
        def handle_request(request):
            nonlocal m3u8_url, referer_url
            if ".m3u8" in request.url:
                m3u8_url = request.url
                # রিকোয়েস্ট হেডার থেকে Referer বের করা (যদি থাকে)
                headers = request.headers
                referer_url = headers.get("referer", "https://crichdsee.st/")

        page.on("request", handle_request)

        try:
            print("Opening target page...")
            # মূল টার্গেট লিংক
            target_page = "https://crichdsee.st/player.php?id=willow"
            await page.goto(target_page, timeout=60000)
            
            # প্লেয়ার লোড হওয়ার জন্য ২০ সেকেন্ড অপেক্ষা করা
            print("Waiting for player to load and fetch stream...")
            await asyncio.sleep(20)

        except Exception as e:
            print(f"Error occurred: {e}")

        await browser.close()

        if m3u8_url:
            # যদি Referer না পাওয়া যায়, তবে ডিফল্ট হিসেবে মূল সাইটের ডোমেইন বা পেজ ব্যবহার করা হবে
            if not referer_url:
                referer_url = "https://crichdsee.st/"

            # আপনি যেভাবে চাচ্ছেন সেই ফরম্যাটে লিংক তৈরি করা (URL|Referer=...)
            final_formatted_link = f"{m3u8_url}|Referer={referer_url}"
            
            print(f"Found Final Link: {final_formatted_link}")
            
            # stream.txt ফাইলে সেভ করা
            with open("stream.txt", "w") as f:
                f.write(final_formatted_link)
        else:
            print("M3U8 link not found!")

if __name__ == "__main__":
    asyncio.run(get_m3u8_link())
