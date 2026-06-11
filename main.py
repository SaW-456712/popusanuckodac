import os
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv

# Включаем логирование ошибок в консоль хостинга
logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    exit()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def fetch_mp3_via_web(sc_url: str) -> tuple[str, str] | tuple[None, None]:
    # Используем альтернативный стабильный шлюз загрузчика
    api_url = f"https://api.soundclouddownloader.org/download?url={sc_url}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success") and "url" in data:
                        title = data.get("title", "track").replace("/", "_")
                        return f"{title}.mp3", data["url"]
                    else:
                        logging.warning(
                            f"API ответило, но ссылки нет: {data}"
                        )
                else:
                    logging.warning(f"Плохой статус ответа API: {response.status}")
        except Exception as e:
            logging.error(f"Ошибка при запросе к Веб-API: {e}")
    return None, None


async def download_file(url: str, dest_path: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    with open(dest_path, "wb") as f:
                        f.write(await response.read())
                    return True
        except Exception as e:
            logging.error(f"Ошибка при сохранении файла: {e}")
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
        except Exception as e:
            logging.error(f"Ошибка отправки аудио в Телеграм: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


async def main():
    logging.info("Бот успешно запущен и слушает сервер...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
