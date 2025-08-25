import logging
import os
import asyncio
import time
from typing import Optional
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# --- ENV ---
load_dotenv()
BOT_TOKEN = "7564998506:AAHqdhSvhtewDEJ5A1LUNRNAp8nSGE2TY64"
FEED_CHANNEL_ID = -1002968547001

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Bot / Dispatcher ---
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# --- Runtime-only owner (reset on restart) ---
OWNER_ID: Optional[int] = None

# --- Startup time to ignore old updates ---
startup_time = int(time.time())


def get_user_tag(message: Message) -> str:
    """Формируем хот-тег автора."""
    user = message.from_user
    if not user:
        return "👤 Unknown"
    if user.username:
        return f"@{user.username}"
    elif user.first_name:
        return user.first_name
    else:
        return f"id:{user.id}"


def format_text(tag: str, text: str) -> str:
    """Формат: @username \\n текст."""
    return f"{tag}\n{text}" if text else tag


async def send_with_tag(message: Message, tag: str):
    """Универсальная пересылка с хот-тегом и переносом строки."""
    # Текст
    if message.text:
        await bot.send_message(
            chat_id=FEED_CHANNEL_ID,
            text=format_text(tag, message.text)
        )

    # Фото
    elif message.photo:
        await bot.send_photo(
            chat_id=FEED_CHANNEL_ID,
            photo=message.photo[-1].file_id,
            caption=format_text(tag, message.caption or "")
        )

    # Видео
    elif message.video:
        await bot.send_video(
            chat_id=FEED_CHANNEL_ID,
            video=message.video.file_id,
            caption=format_text(tag, message.caption or "")
        )

    # Документы
    elif message.document:
        await bot.send_document(
            chat_id=FEED_CHANNEL_ID,
            document=message.document.file_id,
            caption=format_text(tag, message.caption or "")
        )

    # Аудио
    elif message.audio:
        await bot.send_audio(
            chat_id=FEED_CHANNEL_ID,
            audio=message.audio.file_id,
            caption=format_text(tag, message.caption or "")
        )

    # Голосовые
    elif message.voice:
        await bot.send_voice(
            chat_id=FEED_CHANNEL_ID,
            voice=message.voice.file_id,
            caption=format_text(tag, message.caption or "")
        )

    # Видео-сообщения (кружочки)
    elif message.video_note:
        await bot.send_video_note(
            chat_id=FEED_CHANNEL_ID,
            video_note=message.video_note.file_id
        )

    # GIF/анимации
    elif message.animation:
        await bot.send_animation(
            chat_id=FEED_CHANNEL_ID,
            animation=message.animation.file_id,
            caption=format_text(tag, message.caption or "")
        )

    # Стикеры
    elif message.sticker:
        await bot.send_sticker(
            chat_id=FEED_CHANNEL_ID,
            sticker=message.sticker.file_id
        )

    # На случай редких типов
    else:
        await message.send_copy(
            chat_id=FEED_CHANNEL_ID,
            caption=format_text(tag, message.caption or "")
        )


# --- /start: любой пользователь становится владельцем текущей сессии ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    global OWNER_ID
    OWNER_ID = message.from_user.id  # всегда перезаписываем владельца

    me = await bot.get_me()
    info_text = (
        " Бот запущен и готов пересылать сообщения.\n\n"
        f" Владелец: <code>{OWNER_ID}</code>\n"
        f" Bot name: {me.first_name}\n"
        f" Username: @{me.username}\n"
        f" Bot ID: {me.id}\n"
    )
    await message.answer(info_text)


# --- Обычные сообщения ---
@dp.message(F.all())
async def forward_message(message: Message):
    # Игнорируем старые апдейты
    if message.date.timestamp() < startup_time:
        return
    # Игнорируем сообщения текущего владельца
    if OWNER_ID and message.from_user and message.from_user.id == OWNER_ID:
        return

    try:
        await send_with_tag(message, get_user_tag(message))
    except Exception as e:
        logging.error(f"Ошибка пересылки обычного сообщения: {e}")


# --- Бизнес-сообщения ---
@dp.business_message()
async def forward_business_message(message: Message):
    # Игнорируем старые апдейты
    if message.date.timestamp() < startup_time:
        return
    # Игнорируем сообщения текущего владельца
    if OWNER_ID and message.from_user and message.from_user.id == OWNER_ID:
        return

    try:
        await send_with_tag(message, get_user_tag(message))
    except Exception as e:
        logging.error(f"Ошибка пересылки business_message: {e}")


# --- Запуск ---
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
