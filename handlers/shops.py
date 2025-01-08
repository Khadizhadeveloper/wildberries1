from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.common import load_config

router = Router()

@router.message(Command(commands=["shops"]))
async def shops_handler(message: Message):
    config = load_config()
    if not config["shops"]:
        await message.answer("Список магазинов пуст.")
        return
    shop_list = "\n".join(f"- {shop['name']}" for shop in config["shops"])
    await message.answer(f"Сохраненные магазины:\n{shop_list}")
