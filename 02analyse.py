import time
import pickle
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
time.sleep(3)  # Ждем загрузки страницы

# Добавляем cookies в сессию
for cookie in cookies:
    # Меняем домен, чтобы cookies были действительны и для других субдоменов
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
time.sleep(5)  # Первоначальная задержка для загрузки страницы

# Прокручиваем страницу до конца для подгрузки всех элементов
SCROLL_PAUSE_TIME = 2
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Ожидаем появления элементов с нужным классом
wait = WebDriverWait(driver, 30)
wait.until(EC.presence_of_all_elements_located(
    (By.CSS_SELECTOR, ".scalable-preview__image.scalable-preview__image_cover")
))

# Находим все элементы с указанным классом
photo_elements = driver.find_elements(By.CSS_SELECTOR, ".scalable-preview__image.scalable-preview__image_cover")
print("Количество найденных элементов:", len(photo_elements))

# Подключаемся к SQLite базе данных и создаем таблицу, если её нет
conn = sqlite3.connect("photos.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        src TEXT
    )
""")

# Извлекаем значение атрибута src каждого элемента и сохраняем в базу
for elem in photo_elements:
    src = elem.get_attribute("src")
    if src:
        cursor.execute("INSERT INTO photos (src) VALUES (?)", (src,))

conn.commit()
conn.close()

print("Данные успешно сохранены в photos.db")
driver.quit()
