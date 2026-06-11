import os
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    exit()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def fetch_mp3_via_web(sc_url: str) -> tuple[str, str] | tuple[None, None]:
    api_url = f"https://api.soundclouddownloader.org/download?url={sc_url}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success") and "url" in data:
                        title = data.get("title", "track").replace("/", "_")
                        return f"{title}.mp3", data["url"]
        except Exception:
            pass
    return None, None


async def download_file(url: str, dest_path: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    with open(dest_path, "wb") as f:
                        f.write(await response.read())
                    return True
        except Exception:
            pass
    return False


@dp.message(F.text.contains("soundcloud.com"))
async def handle_soundcloud_link(message: Message):
    url = message.text.strip()

    filename, mp3_url = await fetch_mp3_via_web(url)
    if not mp3_url:
        return

    file_path = os.path.join(DOWNLOAD_DIR, filename)
    success = await download_file(mp3_url, file_path)

    if success and os.path.exists(file_path):
        try:
            audio_file = FSInputFile(file_path)
            await message.answer_audio(audio=audio_file)
        except Exception:
            pass
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
