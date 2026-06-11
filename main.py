import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
    exit()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_soundcloud_audio(url: str) -> str | None:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return os.path.splitext(filename)[0] + ".mp3"
    except Exception as e:
        logging.error(f"Ошибка yt-dlp при скачивании: {e}")
        return None


@dp.message(F.text.contains("soundcloud.com"))
async def handle_soundcloud_link(message: Message):
    url = message.text.strip()

    loop = asyncio.get_event_loop()
    file_path = await loop.run_in_executor(None, download_soundcloud_audio, url)

    if file_path and os.path.exists(file_path):
        try:
            audio_file = FSInputFile(file_path)
            await message.answer_audio(audio=audio_file)
        except Exception as e:
            logging.error(f"Ошибка отправки аудио в Телеграм: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


async def main():
    logging.info("Бот запущен через yt-dlp...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
