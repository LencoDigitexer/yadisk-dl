import sqlite3
import os
import requests
from concurrent.futures import ThreadPoolExecutor

# Настройки скачивания
DOWNLOAD_DIR = "downloads"  # Папка для сохранения файлов
THREADS = 4  # Количество потоков
LIMIT = 20  # Сколько файлов скачать (0 = все)

# Создаём папку для загрузок
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Подключаемся к базе данных
conn = sqlite3.connect("links.db")
cursor = conn.cursor()

# Удаляем дубликаты по URL
cursor.execute("""
    DELETE FROM links WHERE id NOT IN (
        SELECT MIN(id) FROM links GROUP BY url
    )
""")
conn.commit()
print("Дубликаты удалены.")

# Загружаем ссылки из базы
cursor.execute("SELECT url, name FROM links ORDER BY id ASC LIMIT ?", (LIMIT,))
links = cursor.fetchall()
conn.close()

print(f"Найдено {len(links)} файлов для скачивания.")

# Функция скачивания
def download_file(url, name):
    # Добавляем https: если ссылка начинается с //
    if url.startswith("//"):
        url = "https:" + url

    if not name:
        name = os.path.basename(url.split("?")[0])  # Если нет имени, берём из URL
    filepath = os.path.join(DOWNLOAD_DIR, name)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Проверяем ошибки

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        print(f"✔ {name} скачан.")
    except requests.RequestException as e:
        print(f"❌ Ошибка скачивания {name}: {e}")

# Запускаем многопоточное скачивание
with ThreadPoolExecutor(max_workers=THREADS) as executor:
    for url, name in links:
        executor.submit(download_file, url, name)

print("✅ Загрузка завершена!")
