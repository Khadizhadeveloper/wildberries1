from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import requests
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,  # Уровень логирования
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Логирование в файл
        logging.StreamHandler()          # Логирование в консоль
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
WB_SALES_URL = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMjE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc1MDY1MDU0NiwiaWQiOiIwMTkzZWYwZS1kMzc0LTcxMjUtODEwZC1jZGJkYjcyYjI0YmQiLCJpaWQiOjU2Mjc5OTIxLCJvaWQiOjEzMDMyMjMsInMiOjEwNzM3NDk3NTgsInNpZCI6IjhkYjJmYmFjLWZjOTUtNDQzMy05OWVhLTE1ZjljNmI5ODUxMiIsInQiOmZhbHNlLCJ1aWQiOjU2Mjc5OTIxfQ.YMl4wjsGjfF00JfP_H6WMNvJainxTmjSC2HyjfHsbQWO1OEPYrrz8S_q-W2BptXLz7ZTIgC0f1n72FJgzEB4ZA"

router = Router()

# Функция для получения данных о продажах
def get_sales_data(api_key, date):
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"dateFrom": date, "dateTo": date}
    try:
        logger.info(f"Запрос данных о продажах за {date}")
        response = requests.get(WB_SALES_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP ошибка при запросе данных за {date}: {e}")
        return f"HTTP ошибка: {e}\nОтвет от API: {response.text}"
    except Exception as e:
        logger.error(f"Неизвестная ошибка при запросе данных за {date}: {e}")
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

    # Получаем текущую дату
    today = datetime.now()

    # Определяем дату начала и окончания в зависимости от выбранного периода
    if period == "today":
        date_from = today.strftime("%Y-%m-%d")
        date_to = date_from
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        date_from = yesterday.strftime("%Y-%m-%d")
        date_to = date_from
    elif period == "last_7_days":
        date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")
    elif period == "custom_period":
        await callback.message.answer("Отправьте дату начала периода (например, 2024-07-01):")
        return  # Ожидаем получения даты начала и окончания периода от пользователя

    try:
        # Получаем данные о продажах
        sales_data = get_sales_data(API_KEY, date_from)

        # Если вернулся текст ошибки, выводим его
        if isinstance(sales_data, str):
            await callback.message.answer(f"Ошибка при запросе данных: {sales_data}")
            return

        # Проверяем, есть ли данные
        if not sales_data:
            await callback.message.answer(f"Нет данных о продажах за {date_from}.")
            return

        # Рассчитываем метрики
        metrics = calculate_metrics(sales_data)

        # Формируем отчет
        report = (
            f"📊 *Отчет о продажах за {date_from}*\n\n"
            f"- 💰 *Общая сумма продаж:* {metrics['total_sales']} руб.\n"
            f"- 📦 *Количество проданных единиц:* {metrics['units_sold']}\n"
            f"- 📊 *Средняя цена продажи:* {metrics['avg_price']:.2f} руб.\n"
            f"- 🏦 *Комиссия Wildberries:* {metrics['total_commission']} руб.\n"
            f"- 💸 *Скидки Wildberries:* {metrics['total_discounts']:.2f} руб.\n"
            f"- 🏧 *Комиссия эквайринга:* {metrics['total_acquiring']:.2f} руб.\n"
            f"- 🚚 *Стоимость логистики:* {metrics['total_logistics']:.2f} руб.\n"
            f"- 📦 *Стоимость хранения:* {metrics['total_storage']} руб.\n"
        )

        await callback.message.answer(report, parse_mode="Markdown")
    except Exception as e:
        await callback.message.answer(f"Ошибка при генерации отчета: {e}")
