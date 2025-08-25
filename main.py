import logging
import os
import asyncio
import time
from dotenv import load_dotenv
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties


# -------- Настройка --------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# --- Храним владельца и канал ---
OWNER_ID: Optional[int] = None
BOUND_CHAT_ID: Optional[int] = None

# Время старта процесса (для отсечения старых апдейтов)
startup_ts = int(time.time())


# -------- /start --------
@dp.message(CommandStart())
async def cmd_start(message: Message):
    global OWNER_ID
    if OWNER_ID is None:
        OWNER_ID = message.from_user.id
        await message.answer(
            "✅ Ты назначен владельцем этого бота.\n"
            "Теперь добавь бота админом в свой канал, чтобы привязать его."
        )
    elif message.from_user.id == OWNER_ID:
        await message.answer("ℹ️ Ты уже являешься владельцем бота.")
    else:
        await message.answer("⛔ У бота уже есть владелец.")


# -------- Привязка при добавлении бота в канал --------
@dp.my_chat_member()
async def bot_added_to_chat(update: ChatMemberUpdated, bot: Bot):
    global OWNER_ID, BOUND_CHAT_ID

    if update.new_chat_member.status in {"administrator", "member"}:
        adder_id = update.from_user.id  # кто добавил
        chat_id = update.chat.id

        if OWNER_ID and adder_id == OWNER_ID:
            BOUND_CHAT_ID = chat_id
            await bot.send_message(
                OWNER_ID,
                f"🔗 Канал/чат <b>{update.chat.title}</b> (id={chat_id}) привязан."
            )
        else:
            # Не владелец — выходим для безопасности
            await bot.leave_chat(chat_id)
            if OWNER_ID:
                await bot.send_message(
                    OWNER_ID,
                    f"⚠️ Кто-то пытался добавить бота в <b>{update.chat.title}</b>, "
                    "но это не твой аккаунт. Бот вышел."
                )


# --- Игнорируем /start в чатах (если прилетит не в личку) ---
@dp.message(CommandStart())
async def ignore_start(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


# -------- Формируем подпись с @username --------
def format_caption(message: Message) -> str:
    user = message.from_user
    if not user:
        return "👤 Unknown"
    username = f"@{user.username}" if user.username else user.full_name
    text = message.text or message.caption or ""
    return f"{username},\n{text}".strip()


# -------- Пересылка обычных сообщений --------
@dp.message(F.text | F.photo | F.video | F.document | F.audio | F.voice | F.sticker | F.animation | F.video_note)
async def forward_message(message: Message):
    global OWNER_ID, BOUND_CHAT_ID

    logging.info(f"[forward_message] id={message.message_id}, "
                 f"business={getattr(message, 'business_connection_id', None)}, "
                 f"chat={message.chat.id}")

    # --- Защиты от дублей/циклов ---
    if not BOUND_CHAT_ID:
        return
    if int(message.date.timestamp()) < startup_ts:
        return
    # если это бизнес-сообщение — не обрабатываем здесь
    if getattr(message, "business_connection_id", None):
        return
    if message.chat and message.chat.id == BOUND_CHAT_ID:
        return
    if (message.from_user and (message.from_user.id == OWNER_ID or message.from_user.is_bot)):
        return

    try:
        caption = format_caption(message)

        if message.text:
            await bot.send_message(BOUND_CHAT_ID, caption)
        else:
            await message.copy_to(
                BOUND_CHAT_ID,
                caption=caption if (message.caption or message.text) else None
            )
    except Exception as e:
        logging.error(f"Ошибка пересылки: {e}")


# --- Хранилище обработанных бизнес-сообщений ---
processed_business_msgs = set()  # (chat_id, business_connection_id, message_id)


@dp.business_message()
async def forward_business_message(message: Message):
    global OWNER_ID, BOUND_CHAT_ID

    business_id = getattr(message, "business_connection_id", None)
    if not business_id:
        return

    key = (message.chat.id, business_id, message.message_id)

    # --- Анти-дубль ---
    if key in processed_business_msgs:
        logging.info(f"[skip duplicate business_message] id={message.message_id}, business={business_id}")
        return
    processed_business_msgs.add(key)

    logging.info(f"[forward_business_message] id={message.message_id}, business={business_id}, chat={message.chat.id}")

    if not BOUND_CHAT_ID:
        return
    if int(message.date.timestamp()) < startup_ts:
        return
    if message.chat and message.chat.id == BOUND_CHAT_ID:
        return
    if message.from_user and (message.from_user.id == OWNER_ID or message.from_user.is_bot):
        return

    try:
        caption = format_caption(message)

        if message.text:
            await bot.send_message(BOUND_CHAT_ID, caption)
        elif message.photo:
            await bot.send_photo(BOUND_CHAT_ID, photo=message.photo[-1].file_id, caption=caption)
        elif message.video:
            await bot.send_video(BOUND_CHAT_ID, video=message.video.file_id, caption=caption)
        elif message.document:
            await bot.send_document(BOUND_CHAT_ID, document=message.document.file_id, caption=caption)
        elif message.audio:
            await bot.send_audio(BOUND_CHAT_ID, audio=message.audio.file_id, caption=caption)
        elif message.voice:
            await bot.send_voice(BOUND_CHAT_ID, voice=message.voice.file_id, caption=caption)
        elif message.video_note:
            await bot.send_video_note(BOUND_CHAT_ID, video_note=message.video_note.file_id)
        elif message.animation:
            await bot.send_animation(BOUND_CHAT_ID, animation=message.animation.file_id, caption=caption)
        elif message.sticker:
            await bot.send_sticker(BOUND_CHAT_ID, sticker=message.sticker.file_id)
        else:
            await bot.send_message(BOUND_CHAT_ID, caption)

    except Exception as e:
        logging.error(f"Ошибка пересылки business_message: {e}")



# -------- Старт --------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
