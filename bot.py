import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import json
from pathlib import Path
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8196919721:AAFmkrZCvB7gr_8amwqK6lshNrPph2UouH4"

# Путь к конфигурационному файлу
CONFIG_PATH = Path("config.json")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


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


# Определяем состояния для FSM
class AddShopStates(StatesGroup):
    waiting_for_api_key = State()
    waiting_for_shop_name = State()

# Обработчик команды /addshop
@dp.message(Command(commands=["addshop"]))
async def addshop_handler(message: Message, state: FSMContext):
    await message.answer("Введите API ключ вашего магазина:")
    await state.set_state(AddShopStates.waiting_for_api_key)

# Обработка ввода API ключа
@dp.message(AddShopStates.waiting_for_api_key)
async def get_api_key_handler(message: Message, state: FSMContext):
    api_key = message.text
    # Здесь можно добавить валидацию API ключа через запрос к Wildberries API
    await state.update_data(api_key=api_key)
    await message.answer("Введите имя магазина:")
    await state.set_state(AddShopStates.waiting_for_shop_name)

# Обработка ввода имени магазина
@dp.message(AddShopStates.waiting_for_shop_name)
async def get_shop_name_handler(message: Message, state: FSMContext):
    shop_name = message.text
    user_data = await state.get_data()
    api_key = user_data["api_key"]

    # Добавляем магазин в конфигурацию
    config["shops"].append({"api_key": api_key, "name": shop_name})
    save_config(config)

    await message.answer(f"Магазин '{shop_name}' успешно добавлен!")
    await state.clear()


# Обработчик команды /delshop
@dp.message(Command(commands=["delshop"]))
async def delshop_handler(message: Message):
    if not config["shops"]:
        await message.answer("Нет сохраненных магазинов.")
        return

    # Формируем кнопки для выбора магазина
    markup = InlineKeyboardMarkup()
    for shop in config["shops"]:
        markup.add(InlineKeyboardButton(shop["name"], callback_data=f"delshop:{shop['name']}"))
    await message.answer("Выберите магазин для удаления:", reply_markup=markup)


# Callback для удаления магазина
@dp.callback_query(lambda c: c.data.startswith("delshop:"))
async def delshop_callback_handler(callback: CallbackQuery):
    shop_name = callback.data.split(":")[1]
    config["shops"] = [shop for shop in config["shops"] if shop["name"] != shop_name]
    save_config(config)
    await callback.message.edit_text(f"Магазин '{shop_name}' удален!")


# Обработчик команды /shops
@dp.message(Command(commands=["shops"]))
async def shops_handler(message: Message):
    if not config["shops"]:
        await message.answer("Список магазинов пуст.")
        return
    shop_list = "\n".join(f"- {shop['name']}" for shop in config["shops"])
    await message.answer(f"Сохраненные магазины:\n{shop_list}")


# Обработчик команды /report
@dp.message(Command(commands=["report"]))
async def report_handler(message: Message):
    if not config["shops"]:
        await message.answer("Сначала добавьте магазины с помощью команды /addshop.")
        return

    # Формируем кнопки для выбора магазина
    markup = InlineKeyboardMarkup()
    for shop in config["shops"]:
        markup.add(InlineKeyboardButton(shop["name"], callback_data=f"report:{shop['name']}"))
    await message.answer("Выберите магазин для генерации отчета:", reply_markup=markup)


# Callback для выбора магазина для отчета
@dp.callback_query(lambda c: c.data.startswith("report:"))
async def report_callback_handler(callback: CallbackQuery):
    shop_name = callback.data.split(":")[1]
    await callback.message.edit_text(f"Генерация отчета для магазина '{shop_name}'...")
    # TODO: Реализовать запрос к API Wildberries и генерацию отчета


# Основная функция запуска
async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
