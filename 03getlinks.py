import time
import pickle
from seleniumwire import webdriver # Используем selenium-wire для перехвата запросов
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

# Открываем страницу входа в Яндекс для установки cookies
driver.get("https://passport.yandex.ru")
time.sleep(3)

# Добавляем cookies в сессию
for cookie in cookies:
    if 'domain' in cookie and "passport.yandex.ru" in cookie['domain']:
        cookie['domain'] = ".yandex.ru"
    if 'expiry' in cookie and isinstance(cookie['expiry'], float):
        cookie['expiry'] = int(cookie['expiry'])
    try:
        driver.add_cookie(cookie)
    except Exception as e:
        print("Не удалось добавить cookie:", cookie, e)

# Переходим на страницу с фотографиями
driver.get("https://disk.yandex.ru/client/photo")
time.sleep(5)  # Ждём загрузки страницы и выполнения запросов

# Перехватываем запрос к API
target_url = "https://disk.yandex.ru/models-v2?m=intapi/photo-get-clusters-with-resources"

for request in driver.requests:
    if target_url in request.url:
        print(f"Запрос найден: {request.url}")
        print(f"Статус: {request.response.status_code}")
        print(f"Заголовки: {request.headers}")
        if request.response:
            print(f"Ответ:\n{request.response.body.decode('utf-8', errors='ignore')}")

time.sleep(10)

driver.quit()
