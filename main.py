import asyncio
import json
import os
from playwright.async_api import async_playwright

# ফোল্ডার এবং ফাইলের নাম কনফিগারেশন
FOLDER_NAME = "Crichd All Channels"
OUTPUT_PLAYLIST = "playlist.m3u"
JSON_FILENAME = "Crichd page Link.json"

# আপনার গিটহাব র (Raw) লিংকের বেস পাথ (আপনার ইউজারনেম এবং রিপোজিটরি নাম অনুযায়ী চেক করে নিবেন)
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/raselmia9/Crichd-Auto-Update/refs/heads/main"

def load_channels():
    """চ্যানেলগুলোর জেসন ফাইল লোড করা"""
    if os.path.exists(JSON_FILENAME):
        with open(JSON_FILENAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

async def fetch_link(channel_id, data):
    name = data.get("name")
    url = data.get("url")
    logo = data.get("logo", "")

    if not url:
        return name, logo, None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # পেজের স্পিড বাড়ানোর জন্য অপ্রয়োজনীয় রিসোর্স ব্লক করা
        await page.route("**/*.{png,jpg,jpeg,gif,css,svg}", lambda route: route.abort())

        m3u8_url = None
        referer_url = "https://crichdsee.st/"

        def handle_request(request):
            nonlocal m3u8_url, referer_url
            if ".m3u8" in request.url and not m3u8_url:
                m3u8_url = request.url
                headers = request.headers
                referer_url = headers.get("referer", referer_url)

        page.on("request", handle_request)

        try:
            await page.goto(url, timeout=30000)
            for _ in range(10):
                if m3u8_url:
                    break
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Error for {name}: {e}")

        await browser.close()

        if m3u8_url:
            return name, logo, m3u8_url, referer_url
        return name, logo, None, None

async def main():
    channels = load_channels()
    if not channels:
        print("No channels found in JSON file!")
        return

    # ফোল্ডার তৈরি করা (যদি না থাকে)
    os.makedirs(FOLDER_NAME, exist_ok=True)

    tasks = [fetch_link(channel_id, data) for channel_id, data in channels.items()]
    results = await asyncio.gather(*tasks)

    playlist_content = "#EXTM3U\n"
    success_count = 0

    for name, logo, stream_link, referer in results:
        if stream_link:
            # ফাইলের নাম থেকে স্পেস বা বিশেষ চরিত্র নিরাপদ করার জন্য (অথবা সরাসরি চ্যানেলের নাম)
            safe_filename = name.replace("/", "-").strip()
            channel_file_name = f"{safe_filename}.m3u8"
            channel_file_path = os.path.join(FOLDER_NAME, channel_file_name)

            # আলাদা চ্যানেলের নিজস্ব .m3u8 ফাইলের কন্টেন্ট তৈরি করা
            channel_m3u8_content = (
                "#EXTM3U\n"
                "#EXT-X-VERSION:3\n"
                "#EXT-X-STREAM-INF:BANDWIDTH=2000000,PROGRAM-ID=1,RESOLUTION=1280x720,FRAME-RATE=25.000\n"
                f"{stream_link}\n"
            )

            # ফোল্ডারের ভেতরে ফাইল সেভ করা
            with open(channel_file_path, "w", encoding="utf-8") as cf:
                cf.write(channel_m3u8_content)

            # গিটহাব র (Raw) লিংক ফরম্যাট তৈরি (স্পেসের জায়গায় %20 হ্যান্ডেল করার জন্য)
            encoded_folder_name = FOLDER_NAME.replace(" ", "%20")
            encoded_file_name = channel_file_name.replace(" ", "%20")
            raw_file_url = f"{GITHUB_RAW_BASE}/{encoded_folder_name}/{encoded_file_name}"

            # মূল প্লেলিস্টের জন্য পাথ এবং রেফারার যুক্ত করা
            final_link_with_referer = f"{raw_file_url}|Referer={referer}"

            playlist_content += f'#EXTINF:-1 tvg-id="" tvg-name="{name}" tvg-logo="{logo}" group-title="Live Sports",{name}\n'
            playlist_content += f"{final_link_with_referer}\n"
            
            print(f"Success: {name}")
            success_count += 1
        else:
            print(f"Failed: {name} (Link not found)")

    # মূল প্লেলিস্ট ফাইল সেভ করা
    with open(OUTPUT_PLAYLIST, "w", encoding="utf-8") as f:
        f.write(playlist_content)
    
    print(f"\nPlaylist generated successfully! Total success: {success_count}/{len(channels)}")

if __name__ == "__main__":
    asyncio.run(main())
