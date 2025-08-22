import logging
import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties


# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = "7564998506:AAHqdhSvhtewDEJ5A1LUNRNAp8nSGE2TY64"
FEED_CHANNEL_ID = -1002968547001

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


# --- Игнорируем команды /start ---
@dp.message(CommandStart())
async def ignore_start(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


# --- Обычные сообщения ---
@dp.message(F.text | F.photo | F.video | F.document | F.audio | F.voice | F.sticker | F.animation)
async def forward_message(message: Message):
    try:
        await message.forward(chat_id=FEED_CHANNEL_ID)
    except Exception as e:
        logging.error(f"Ошибка пересылки обычного сообщения: {e}")


# --- Бизнес-сообщения ---
@dp.business_message()
async def forward_business_message(message: Message):
    try:
        await message.send_copy(chat_id=FEED_CHANNEL_ID)
    except Exception as e:
        logging.error(f"Ошибка копирования business_message: {e}")


# --- Запуск ---
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
