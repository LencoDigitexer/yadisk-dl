import time
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import chromedriver_autoinstaller

# Устанавливаем ChromeDriver, если он отсутствует
chromedriver_autoinstaller.install()

# Настройки браузера
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=options)

def login_yandex():
    driver.get("https://passport.yandex.ru/auth")
    
    print("Введите логин и пароль вручную, затем нажмите Enter в консоли")
    input("Нажмите Enter после завершения авторизации...")
    
    # Сохранение cookies после успешного входа
    with open("session.pkl", "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    print("Сессия сохранена в session.pkl")

    driver.quit()

if __name__ == "__main__":
    login_yandex()
