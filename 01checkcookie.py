import time
import pickle
from selenium import webdriver
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

# Открываем страницу passport.yandex.ru для установки cookies
driver.get("https://passport.yandex.ru")
time.sleep(3)

# Добавляем cookies в сессию
for cookie in cookies:
    # Если домен cookies относится к passport.yandex.ru, изменим его на общий домен .yandex.ru,
    # чтобы он действовал на id.yandex.ru
    if 'domain' in cookie and "passport.yandex.ru" in cookie['domain']:
        cookie['domain'] = ".yandex.ru"
    # Если expiry представлен в виде float, приводим к int
    if 'expiry' in cookie and isinstance(cookie['expiry'], float):
        cookie['expiry'] = int(cookie['expiry'])
    try:
        driver.add_cookie(cookie)
    except Exception as e:
        print("Не удалось добавить cookie:", cookie, e)

# Переходим на сайт id.yandex.ru
driver.get("https://id.yandex.ru")
time.sleep(5)  # Ждём загрузки страницы

# Делаем скриншот страницы
screenshot_path = "id_yandex_screenshot.png"
driver.save_screenshot(screenshot_path)
print(f"Скриншот страницы сохранён как {screenshot_path}")

driver.quit()
