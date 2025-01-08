from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import requests

# Конфигурация
WB_SALES_URL = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMjE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc1MDY1MDU0NiwiaWQiOiIwMTkzZWYwZS1kMzc0LTcxMjUtODEwZC1jZGJkYjcyYjI0YmQiLCJpaWQiOjU2Mjc5OTIxLCJvaWQiOjEzMDMyMjMsInMiOjEwNzM3NDk3NTgsInNpZCI6IjhkYjJmYmFjLWZjOTUtNDQzMy05OWVhLTE1ZjljNmI5ODUxMiIsInQiOmZhbHNlLCJ1aWQiOjU2Mjc5OTIxfQ.YMl4wjsGjfF00JfP_H6WMNvJainxTmjSC2HyjfHsbQWO1OEPYrrz8S_q-W2BptXLz7ZTIgC0f1n72FJgzEB4ZA"

router = Router()

# Функция для получения данных о продажах
def get_sales_data(api_key, date):
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"dateFrom": date, "dateTo": date}
    try:
        response = requests.get(WB_SALES_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return f"HTTP ошибка: {e}\nОтвет от API: {response.text}"
    except Exception as e:
        return f"Неизвестная ошибка: {e}"

# Функция для расчета метрик
def calculate_metrics(sales_data):
    total_sales = sum(item.get("totalPrice", 0) for item in sales_data)  # Общая сумма продаж
    total_commission = sum(item.get("paymentSaleAmount", 0) for item in sales_data)  # Комиссия Wildberries
    total_discounts = sum(item.get("discountPercent", 0) * item.get("totalPrice", 0) / 100 for item in sales_data)  # Скидки Wildberries
    total_acquiring = sum((item.get("forPay", 0) * item.get("spp", 0) / 100) for item in sales_data)  # Комиссия эквайринга
    total_logistics = sum(item.get("finishedPrice", 0) - item.get("forPay", 0) for item in sales_data)  # Стоимость логистики
    total_storage = 0  # Стоимость хранения: отсутствует в данных
    units_sold = len(sales_data)  # Количество проданных единиц
    avg_price = total_sales / units_sold if units_sold > 0 else 0  # Средняя цена продажи

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
@router.message(Command(commands=["report"]))
async def report_handler(message: Message):
    # Создаем кнопки для выбора действия
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отчет за 2024-07-20", callback_data="report:2024-07-20")]
    ])
    await message.answer("Выберите действие:", reply_markup=markup)

# Обработчик кнопки "Отчет за 2024-07-20"
@router.callback_query(lambda c: c.data.startswith("report:"))
async def report_callback_handler(callback: CallbackQuery):
    date = callback.data.split(":")[1]  # Получаем дату из callback_data

    try:
        # Получаем данные о продажах
        sales_data = get_sales_data(API_KEY, date)

        # Если вернулся текст ошибки, выводим его
        if isinstance(sales_data, str):
            await callback.message.answer(f"Ошибка при запросе данных: {sales_data}")
            return

        # Проверяем, есть ли данные
        if not sales_data:
            await callback.message.answer(f"Нет данных о продажах за {date}.")
            return

        # Рассчитываем метрики
        metrics = calculate_metrics(sales_data)

        # Формируем отчет
        report = (
            f"📊 *Отчет о продажах за {date}*\n\n"
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
