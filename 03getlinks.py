import time
import pickle
import sqlite3
import json
from seleniumwire import webdriver  # Используем selenium-wire для перехвата запросов
import chromedriver_autoinstaller

# Устанавливаем ChromeDriver, если он отсутствует
chromedriver_autoinstaller.install()

# Настройки браузера
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options=options)

# Загружаем сохранённые cookies из session.pkl
with open("session.pkl", "rb") as f:
    cookies = pickle.load(f)

# Открываем страницу входа Яндекса для установки cookies
driver.get("https://passport.yandex.ru")
time.sleep(3)

# Добавляем cookies в сессию
for cookie in cookies:
    # Приводим домен к общему виду
    if 'domain' in cookie and "passport.yandex.ru" in cookie['domain']:
        cookie['domain'] = ".yandex.ru"
    if 'expiry' in cookie and isinstance(cookie['expiry'], float):
        cookie['expiry'] = int(cookie['expiry'])
    try:
        driver.add_cookie(cookie)
    except Exception as e:
        print("Не удалось добавить cookie:", cookie, e)

# Переходим на страницу с фотографиями на Яндекс.Диске
driver.get("https://disk.yandex.ru/client/photo")
time.sleep(5)  # Ждем загрузки страницы и выполнения запросов

# Задаем целевой URL запроса
target_url = "https://disk.yandex.ru/models-v2?m=intapi/photo-get-clusters-with-resources"

# Ищем нужный запрос среди перехваченных
target_request = None
for request in driver.requests:
    if target_url in request.url and request.response:
        target_request = request
        break

if target_request is None:
    print("Запрос не найден или ответ отсутствует.")
    driver.quit()
    exit(1)

# Декодируем тело ответа
try:
    response_body = target_request.response.body.decode('utf-8', errors='ignore')
    data = json.loads(response_body)
except Exception as e:
    print("Ошибка при разборе ответа:", e)
    driver.quit()
    exit(1)

# Извлекаем список элементов из resources -> fetched
fetched = data.get("resources", {}).get("fetched", [])
print(f"Найдено {len(fetched)} элементов в 'fetched'.")

# Собираем ссылки из каждого элемента: meta -> sizes[0] -> url
links = []
for item in fetched:
    meta = item.get("meta", {})
    photo_name = item.get("name", {})
    sizes = meta.get("sizes", [])
    if sizes and isinstance(sizes, list):
        # Берем первый элемент массива sizes и его url
        first_size = sizes[0]
        url = first_size.get("url")
        if url:
            links.append(url)

print(f"Извлечено ссылок: {len(links)}")
for link in links:
    print(link)

# Сохраняем ссылки в базу данных SQLite
conn = sqlite3.connect("links.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT
        name TEXT
    )
""")

for url in links:
    cursor.execute("INSERT INTO links (url) VALUES (?)", (url,))

conn.commit()
conn.close()

print("Ссылки успешно сохранены в базе данных links.db")
driver.quit()
