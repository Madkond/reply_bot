import os
import logging
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import BusinessConnection, BusinessMessagesDeleted, Message
from aiogram.client.default import DefaultBotProperties
import asyncio

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Конфигурация
API_TOKEN = "6288342219:AAELGG0RjPjppMvuCS7xdPgW4F4w7Eq-5ls"
FEED_CHANNEL_ID = -1001552937015

# Инициализация бота с правильными параметрами
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Создаем диспетчер и роутер
dp = Dispatcher()
business_router = Router()
dp.include_router(business_router)

# Глобальные переменные для управления бизнес-соединениями
active_connections = {}


@business_router.business_connection()
async def handle_business_connect(business_connection: BusinessConnection):
    """Обработчик подключения нового бизнес-соединения"""
    logger.info(f"Новое бизнес-соединение: {business_connection.id}")
    active_connections[business_connection.id] = business_connection
    await bot.send_message(
        chat_id=business_connection.user_chat_id,
        text=" Ваш чат подключен ",
    )


@business_router.message(F.business_connection_id != None)
async def handle_business_message(message: Message):
    """Обработчик сообщений из бизнес-чатов"""
    try:
        # Пропускаем служебные сообщения
        if not message.text and not message.caption and not message.media:
            return

        # Получаем информацию о бизнес-соединении
        connection_id = message.business_connection_id
        connection = active_connections.get(connection_id)

        if not connection:
            logger.warning(f"Неизвестное соединение: {connection_id}")
            return

        # Получаем информацию о чате
        chat_id = message.chat.id
        try:
            chat_info = await bot.get_chat(chat_id)
        except Exception as e:
            logger.error(f"Ошибка получения чата {chat_id}: {str(e)}")
            chat_info = types.Chat(id=chat_id, type="unknown", title="Неизвестный чат")

        # Форматируем информацию об отправителе
        sender = message.from_user
        sender_name = format_name(sender)
        sender_link = f"@{sender.username}" if sender and sender.username else f"tg://user?id={sender.id}" if sender else "N/A"

        # Форматируем информацию о чате
        if chat_info.type == "private":
            chat_title = f"👤 {sender_name}" if sender_name else "👤 Личный чат"
        else:
            chat_title = f"👥 {chat_info.title}" if hasattr(chat_info,
                                                           'title') and chat_info.title else "👥 Групповой чат"

        # Форматируем сообщение для канала
        caption = (
            f"📩 <b>Сообщение из:</b> {chat_title}\n"
            f"👤 <b>Отправитель:</b> <a href='{sender_link}'>{sender_name or 'Аноним'}</a>\n"
            f"🆔 <b>Чат ID:</b> <code>{chat_id}</code>\n\n"
        )

        # Добавляем текст сообщения
        if message.text:
            caption += message.text
        elif message.caption:
            caption += message.caption

        # Пересылаем в канал
        if message.photo:
            await bot.send_photo(
                chat_id=FEED_CHANNEL_ID,
                photo=message.photo[-1].file_id,
                caption=caption
            )
        elif message.video:
            await bot.send_video(
                chat_id=FEED_CHANNEL_ID,
                video=message.video.file_id,
                caption=caption
            )
        elif message.document:
            await bot.send_document(
                chat_id=FEED_CHANNEL_ID,
                document=message.document.file_id,
                caption=caption
            )
        elif message.sticker:
            await bot.send_message(
                chat_id=FEED_CHANNEL_ID,
                text=f"{caption}Стикер: {message.sticker.emoji}",
            )
        else:
            await bot.send_message(
                chat_id=FEED_CHANNEL_ID,
                text=caption,
                disable_web_page_preview=True
            )

        logger.info(f"Переслано сообщение из чата {chat_id}")

    except Exception as e:
        logger.error(f"Ошибка обработки: {str(e)}", exc_info=True)


@business_router.deleted_business_messages()
async def handle_deleted_messages(event: BusinessMessagesDeleted):
    """Обработчик удаленных сообщений"""
    logger.info(f"Удалены сообщения в чате {event.chat_id}")


def format_name(user: types.User) -> str:
    """Форматирует имя пользователя"""
    if not user:
        return "Аноним"
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    return name.strip()


@dp.message(Command("connections"))
async def list_connections(message: types.Message):
    """Показывает активные бизнес-соединения"""
    if not active_connections:
        await message.answer(" Нет активных соединений")
        return

    text = " Активные бизнес-соединения:\n\n"
    for conn_id, conn in active_connections.items():
        text += f"• ID: <code>{conn_id}</code>\n"
        text += f"  Пользователь: <code>{conn.user_chat_id}</code>\n"
        text += f"  Дата: {conn.date}\n\n"

    await message.answer(text)


@dp.message(Command("help", "start"))
async def send_help(message: types.Message):
    """Отправляет инструкцию по использованию"""
    help_text = (
        " <b>Бот для пересылки сообщений</b>\n\n"
        "Для работы необходимо:\n"
        "1. Добавить бота как обработчик сообщений в настройках Telegram Business\n"
        "2. Подключить нужные чаты в разделе 'Боты-обработчики'\n\n"
        "Команды:\n"
        "/connections - Показать активные соединения\n"
        "/help - Эта справка"
    )
    await message.answer(help_text)


async def main():
    logger.info("Запуск бизнес-бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())