import asyncio
import json
import os
from playwright.async_api import async_playwright

# জেসন ফাইল থেকে চ্যানেল লিস্ট লোড করার ফাংশন
def load_channels():
    json_filename = "Crichd page Link.json"
    if os.path.exists(json_filename):
        with open(json_filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

async def fetch_link(name, url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # গতি বাড়ানোর জন্য ইমেজ, বিজ্ঞাপন ও অন্যান্য ফালতু ফাইল ব্লক করা
        await page.route("**/*.{png,jpg,jpeg,gif,css,svg}", lambda route: route.abort())

        m3u8_url = None
        referer_url = "https://crichdsee.st/"

        def handle_request(request):
            nonlocal m3u8_url, referer_url
            if ".m3u8" in request.url:
                m3u8_url = request.url
                headers = request.headers
                referer_url = headers.get("referer", "https://crichdsee.st/")

        page.on("request", handle_request)

        try:
            # পেজ ভিজিট করা
            await page.goto(url, timeout=30000)
            
            # লিংক পাওয়ার জন্য সর্বোচ্চ ১০ সেকেন্ড অপেক্ষা করা
            for _ in range(10):
                if m3u8_url:
                    break
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error for {name}: {e}")

        await browser.close()

        if m3u8_url:
            return name, f"{m3u8_url}|Referer={referer_url}"
        return name, None

async def main():
    channels = load_channels()
    if not channels:
        print("No channels found in JSON file!")
        return

    # একসাথে সব চ্যানেলের কাজ শুরু করা
    tasks = [fetch_link(name, url) for name, url in channels.items()]
    results = await asyncio.gather(*tasks)

    # স্ট্যান্ডার্ড M3U প্লেলিস্ট ফরম্যাটে ফাইল তৈরি করা
    playlist_content = "#EXTM3U\n"
    
    for name, stream_link in results:
        if stream_link:
            playlist_content += f'#EXTINF:-1 tvg-id="" tvg-name="{name}" group-title="Live Sports",{name}\n'
            playlist_content += f"{stream_link}\n"
            print(f"Success: {name}")
        else:
            print(f"Failed: {name} (Link not found)")

    # প্লেলিস্টটি playlist.m3u ফাইলে সেভ করা
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(playlist_content)
    
    print("Playlist generated successfully as 'playlist.m3u'!")

if __name__ == "__main__":
    asyncio.run(main())
