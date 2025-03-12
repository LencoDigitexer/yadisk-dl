import time
import pickle
import sqlite3
import json
from seleniumwire import webdriver  # Перехват запросов
import chromedriver_autoinstaller
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Устанавливаем ChromeDriver, если отсутствует
chromedriver_autoinstaller.install()

# Настройки браузера
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options=options)

# Загружаем cookies
with open("session.pkl", "rb") as f:
    cookies = pickle.load(f)

# Открываем страницу входа Яндекса
driver.get("https://passport.yandex.ru")
time.sleep(3)

# Устанавливаем cookies
for cookie in cookies:
    if 'domain' in cookie and "passport.yandex.ru" in cookie['domain']:
        cookie['domain'] = ".yandex.ru"
    if 'expiry' in cookie and isinstance(cookie['expiry'], float):
        cookie['expiry'] = int(cookie['expiry'])
    try:
        driver.add_cookie(cookie)
    except Exception as e:
        print("Не удалось добавить cookie:", cookie, e)

# Переход на страницу с фотографиями
driver.get("https://disk.yandex.ru/client/photo")
time.sleep(5)

# Настройка базы данных
conn = sqlite3.connect("links.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        name TEXT
    )
""")
conn.commit()

# Функция обработки запроса
def process_request(request):
    try:
        response_body = request.response.body.decode('utf-8', errors='ignore')
        data = json.loads(response_body)

        fetched = data.get("resources", {}).get("fetched", [])
        new_links = []

        for item in fetched:
            meta = item.get("meta", {})
            photo_name = item.get("name", "")
            sizes = meta.get("sizes", [])

            if sizes and isinstance(sizes, list):
                first_size = sizes[0]
                url = first_size.get("url")

                if url:
                    new_links.append((url, photo_name))

        # Добавляем только новые ссылки
        cursor.executemany("INSERT OR IGNORE INTO links (url, name) VALUES (?, ?)", new_links)
        conn.commit()

        print(f"Добавлено {len(new_links)} новых ссылок.")

    except Exception as e:
        print("Ошибка при обработке запроса:", e)

# Прокрутка с эмуляцией колеса мыши
SCROLL_PAUSE_TIME = 0.01
previous_requests = set()
actions = ActionChains(driver)

while True:
    

    # Проверяем новые запросы
    new_requests = 0
    for request in driver.requests:
        if request.url.startswith("https://disk.yandex.ru/models-v2?m=intapi/photo-get-clusters-with-resources"):
            if request.id not in previous_requests and request.response:
                previous_requests.add(request.id)
                process_request(request)
                new_requests += 1

    # Медленная прокрутка вниз (эмуляция колеса мыши)
    for _ in range(3):  # Делаем 3 небольших прокрутки
        actions.send_keys(Keys.PAGE_DOWN).perform()
        time.sleep(0.01)

    time.sleep(SCROLL_PAUSE_TIME)  # Ждём загрузки новых данных

    
    # Если за несколько итераций нет новых данных, завершаем
    if new_requests == 0:
        print("Новых данных нет, прекращаем работу.")
        

# Закрываем соединение
conn.close()
driver.quit()
