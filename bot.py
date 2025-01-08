import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import json
import requests
from pathlib import Path
from aiogram.filters import Command
from handlers.addshop import router as add_shop
from handlers.delshop import router as del_shop
from handlers.shops import router as shops
from handlers.report import router as report

import sys
sys.stdout.reconfigure(encoding="utf-8")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

WB_SALES_URL = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"


# Токен бота
BOT_TOKEN = "8196919721:AAFmkrZCvB7gr_8amwqK6lshNrPph2UouH4"

# Путь к конфигурационному файлу
CONFIG_PATH = Path("config.json")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(add_shop)
dp.include_router(report)
dp.include_router(shops)
dp.include_router(del_shop)


# Функция для загрузки конфигурации
def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"shops": []}


# Функция для сохранения конфигурации
def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


# Загружаем конфигурацию
config = load_config()


# Обработчик команды /start
@dp.message(Command(commands=["start"]))
async def start_handler(message: Message):
    await message.answer(
        "Привет! Я бот для аналитики продаж на Wildberries. Используйте /help для получения списка команд.")


# Обработчик команды /help
@dp.message(Command(commands=["help"]))
async def help_handler(message: Message):
    commands = (
        "/start - Начало работы с ботом\n"
        "/addshop - Добавить магазин\n"
        "/delshop - Удалить магазин\n"
        "/shops - Показать список магазинов\n"
        "/report - Получить отчет о продажах"
    )
    await message.answer(f"Доступные команды:\n{commands}")



# Основная функция запуска
async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
