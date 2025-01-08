import requests
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.common import load_config, save_config

router = Router()

# URL для проверки API-ключа
WB_TEST_URL = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"

# Определяем состояния для FSM
class AddShopStates(StatesGroup):
    waiting_for_api_key = State()
    waiting_for_shop_name = State()

# Функция для проверки API-ключа
def validate_api_key(api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"dateFrom": "2023-01-01", "dateTo": "2023-01-01"}  # Дата без продаж
    try:
        response = requests.get(WB_TEST_URL, headers=headers, params=params)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        return f"Ошибка: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Неизвестная ошибка: {e}"

@router.message(Command(commands=["addshop"]))
async def addshop_handler(message: Message, state: FSMContext):
    await message.answer("Введите API ключ вашего магазина:")
    await state.set_state(AddShopStates.waiting_for_api_key)

@router.message(AddShopStates.waiting_for_api_key)
async def get_api_key_handler(message: Message, state: FSMContext):
    api_key = message.text

    # Проверяем ключ
    validation_result = validate_api_key(api_key)
    if validation_result is not True:
        await message.answer(f"Неверный API ключ. Ошибка: {validation_result}\nПопробуйте снова:")
        return  # Ожидаем новый ввод API-ключа

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
    config.setdefault("shops", []).append({"api_key": api_key, "name": shop_name})
    save_config(config)

    await message.answer(f"Магазин '{shop_name}' успешно добавлен!")
    await state.clear()
