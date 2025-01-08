from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import requests
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

WB_SALES_URL = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMjE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc1MDY1MDU0NiwiaWQiOiIwMTkzZWYwZS1kMzc0LTcxMjUtODEwZC1jZGJkYjcyYjI0YmQiLCJpaWQiOjU2Mjc5OTIxLCJvaWQiOjEzMDMyMjMsInMiOjEwNzM3NDk3NTgsInNpZCI6IjhkYjJmYmFjLWZjOTUtNDQzMy05OWVhLTE1ZjljNmI5ODUxMiIsInQiOmZhbHNlLCJ1aWQiOjU2Mjc5OTIxfQ.YMl4wjsGjfF00JfP_H6WMNvJainxTmjSC2HyjfHsbQWO1OEPYrrz8S_q-W2BptXLz7ZTIgC0f1n72FJgzEB4ZA"

router = Router()

user_data = {}  # Словарь для временного хранения данных пользователя



def get_sales_data(api_key, date_from, date_to):
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"dateFrom": date_from, "dateTo": date_to}
    try:
        logger.info(f"Запрос данных о продажах с {date_from} по {date_to}")
        response = requests.get(WB_SALES_URL, headers=headers, params=params)
        response.encoding = "utf-8"  # Установка корректной кодировки
        logger.info(f"Ответ от API (до обработки): {response.text[:500]}")
        # Проверка на валидный JSON
        if not response.text.strip().startswith("[") or not response.text.strip().endswith("]"):
            logger.error("Ответ API не является корректным JSON.")
            return "Ошибка: некорректный формат данных."
        # Парсинг JSON
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP ошибка: {e}")
        return f"HTTP ошибка: {e}\nОтвет от API: {response.text[:500]}"
    except ValueError as e:
        logger.error(f"Ошибка при парсинге JSON: {e}")
        return f"Ошибка при парсинге данных: {e}"
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        return f"Неизвестная ошибка: {e}"



# Функция для расчета метрик
def calculate_metrics(sales_data):
    logger.info("Рассчитываем метрики продаж")
    total_sales = sum(item.get("totalPrice", 0) for item in sales_data)
    total_commission = sum(item.get("paymentSaleAmount", 0) for item in sales_data)
    total_discounts = sum(item.get("discountPercent", 0) * item.get("totalPrice", 0) / 100 for item in sales_data)
    total_acquiring = sum((item.get("forPay", 0) * item.get("spp", 0) / 100) for item in sales_data)
    total_logistics = sum(item.get("finishedPrice", 0) - item.get("forPay", 0) for item in sales_data)
    total_storage = 0
    units_sold = len(sales_data)
    avg_price = total_sales / units_sold if units_sold > 0 else 0

    return {
        "total_sales": total_sales,
        "total_commission": total_commission,
        "total_discounts": total_discounts,
        "total_acquiring": total_acquiring,
        "total_logistics": total_logistics,
        "total_storage": total_storage,
        "units_sold": units_sold,
        "avg_price": avg_price,
    }


# Обработчик команды /report
@router.message(Command("report"))
async def report_handler(message: Message):
    logger.info(f"Получена команда /report от пользователя {message.from_user.id}")
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сегодня", callback_data="period:today")],
        [InlineKeyboardButton(text="Вчера", callback_data="period:yesterday")],
        [InlineKeyboardButton(text="Последние 7 дней", callback_data="period:last_7_days")],
        [InlineKeyboardButton(text="Произвольный период", callback_data="period:custom_period")],
    ])
    await message.answer("Выберите период для отчета:", reply_markup=markup)


# Обработчик выбора периода
@router.callback_query(lambda c: c.data.startswith("period:"))
async def period_callback_handler(callback: CallbackQuery):
    logger.info(f"Получен callback {callback.data} от пользователя {callback.from_user.id}")
    period = callback.data.split(":")[1]

    today = datetime.now()

    if period == "today":
        date_from = date_to = today.strftime("%Y-%m-%d")
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        date_from = date_to = yesterday.strftime("%Y-%m-%d")
    elif period == "last_7_days":
        date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")
    elif period == "custom_period":
        user_data[callback.from_user.id] = {"step": "start_date"}
        await callback.message.answer("Введите начальную дату в формате ГГГГ-ММ-ДД:")
        return

    await generate_report(callback.message, date_from, date_to)


# Обработчик ввода начальной и конечной даты
@router.message()
async def handle_custom_dates(message: Message):
    user_id = message.from_user.id

    if user_id in user_data and "step" in user_data[user_id]:
        step = user_data[user_id]["step"]

        if step == "start_date":
            try:
                start_date = datetime.strptime(message.text, "%Y-%m-%d").strftime("%Y-%m-%d")
                user_data[user_id]["start_date"] = start_date
                user_data[user_id]["step"] = "end_date"
                await message.answer("Введите конечную дату в формате ГГГГ-ММ-ДД:")
            except ValueError:
                await message.answer("Неверный формат даты. Попробуйте снова (ГГГГ-ММ-ДД).")

        elif step == "end_date":
            try:
                end_date = datetime.strptime(message.text, "%Y-%m-%d").strftime("%Y-%m-%d")
                start_date = user_data[user_id]["start_date"]

                del user_data[user_id]  # Очищаем данные пользователя

                await generate_report(message, start_date, end_date)
            except ValueError:
                await message.answer("Неверный формат даты. Попробуйте снова (ГГГГ-ММ-ДД).")


async def generate_report(message, date_from, date_to):
    try:
        sales_data = get_sales_data(API_KEY, date_from, date_to)

        if isinstance(sales_data, str):
            await message.answer(f"Ошибка при запросе данных: {sales_data}")
            return

        if not sales_data:
            await message.answer(f"Нет данных о продажах с {date_from} по {date_to}.")
            return

        metrics = calculate_metrics(sales_data)

        report = (
            f"📊 *Отчет о продажах с {date_from} по {date_to}*\n\n"
            f"- 💰 *Общая сумма продаж:* {metrics['total_sales']} руб.\n"
            f"- 📦 *Количество проданных единиц:* {metrics['units_sold']}\n"
            f"- 📊 *Средняя цена продажи:* {metrics['avg_price']:.2f} руб.\n"
            f"- 🏦 *Комиссия Wildberries:* {metrics['total_commission']} руб.\n"
            f"- 💸 *Скидки Wildberries:* {metrics['total_discounts']:.2f} руб.\n"
            f"- 🏧 *Комиссия эквайринга:* {metrics['total_acquiring']:.2f} руб.\n"
            f"- 🚚 *Стоимость логистики:* {metrics['total_logistics']:.2f} руб.\n"
            f"- 📦 *Стоимость хранения:* {metrics['total_storage']} руб.\n"
        )

        await message.answer(report, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка при генерации отчета: {e}")
        await message.answer(f"Ошибка при генерации отчета: {e}")

