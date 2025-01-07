import httpx

# Конфигурация
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMjE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc1MDY1MDU0NiwiaWQiOiIwMTkzZWYwZS1kMzc0LTcxMjUtODEwZC1jZGJkYjcyYjI0YmQiLCJpaWQiOjU2Mjc5OTIxLCJvaWQiOjEzMDMyMjMsInMiOjEwNzM3NDk3NTgsInNpZCI6IjhkYjJmYmFjLWZjOTUtNDQzMy05OWVhLTE1ZjljNmI5ODUxMiIsInQiOmZhbHNlLCJ1aWQiOjU2Mjc5OTIxfQ.YMl4wjsGjfF00JfP_H6WMNvJainxTmjSC2HyjfHsbQWO1OEPYrrz8S_q-W2BptXLz7ZTIgC0f1n72FJgzEB4ZA"
HEADERS = {"Authorization": API_KEY}

# Список эндпоинтов
ENDPOINTS = {
    "orders": "https://statistics-api.wildberries.ru/api/v1/supplier/orders",
    "sales": "https://statistics-api.wildberries.ru/api/v1/supplier/sales",
    "stocks": "https://statistics-api.wildberries.ru/api/v1/supplier/stocks",
    "feedbacks": "https://feedbacks-api.wildberries.ru/api/v1/feedbacks/count"
}

def test_endpoint(endpoint_name, url, params=None):
    """Тестирует указанный эндпоинт."""
    print(f"\nТестирование эндпоинта '{endpoint_name}'...")
    try:
        response = httpx.get(url, headers=HEADERS, params=params)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text[:500]}")  # Ограничим вывод текста
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка при запросе к '{endpoint_name}': {e}")
        return False

if __name__ == "__main__":
    # Тестируем каждый эндпоинт
    for name, url in ENDPOINTS.items():
        params = None

        # Пример параметров для заказов и продаж
        if name in ["orders", "sales"]:
            params = {
                "dateFrom": "2023-01-01",
                "dateTo": "2023-01-10"
            }

        # Тестируем эндпоинт
        is_valid = test_endpoint(name, url, params=params)
        if is_valid:
            print(f"Эндпоинт '{name}' успешно отвечает!")
        else:
            print(f"Проблема с эндпоинтом '{name}'.")
