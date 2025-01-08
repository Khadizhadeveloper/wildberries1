from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.common import load_config, save_config

router = Router()

# Определяем состояния для FSM
class AddShopStates(StatesGroup):
    waiting_for_api_key = State()
    waiting_for_shop_name = State()

@router.message(Command(commands=["addshop"]))
async def addshop_handler(message: Message, state: FSMContext):
    await message.answer("Введите API ключ вашего магазина:")
    await state.set_state(AddShopStates.waiting_for_api_key)

@router.message(AddShopStates.waiting_for_api_key)
async def get_api_key_handler(message: Message, state: FSMContext):
    api_key = message.text
    await state.update_data(api_key=api_key)
    await message.answer("Введите имя магазина:")
    await state.set_state(AddShopStates.waiting_for_shop_name)

@router.message(AddShopStates.waiting_for_shop_name)
async def get_shop_name_handler(message: Message, state: FSMContext):
    shop_name = message.text
    user_data = await state.get_data()
    api_key = user_data["api_key"]

    # Сохраняем магазин в конфигурацию
    config = load_config()
    config["shops"].append({"api_key": api_key, "name": shop_name})
    save_config(config)

    await message.answer(f"Магазин '{shop_name}' успешно добавлен!")
    await state.clear()
