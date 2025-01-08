from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.common import load_config, save_config

router = Router()

@router.message(Command(commands=["delshop"]))
async def delshop_handler(message: Message):
    # Загружаем конфигурацию
    config = load_config()

    # Проверяем наличие сохраненных магазинов
    if not config.get("shops", []):
        await message.answer("Нет сохраненных магазинов.")
        return

    # Генерируем клавиатуру для удаления магазинов
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=shop["name"], callback_data=f"delshop:{shop['name']}")]
            for shop in config["shops"]
        ]
    )

    await message.answer("Выберите магазин для удаления:", reply_markup=markup)

@router.callback_query(lambda c: c.data.startswith("delshop:"))
async def delshop_callback_handler(callback: CallbackQuery):
    # Получаем имя магазина из callback_data
    shop_name = callback.data.split(":")[1]

    # Загружаем конфигурацию
    config = load_config()

    # Удаляем магазин из списка
    new_shops = [shop for shop in config.get("shops", []) if shop["name"] != shop_name]
    config["shops"] = new_shops
    save_config(config)

    # Отвечаем пользователю
    await callback.message.edit_text(f"Магазин '{shop_name}' удален!")
