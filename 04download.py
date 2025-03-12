import sqlite3
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm  # Для отображения прогресса

# Настройки скачивания
DOWNLOAD_DIR = "downloads"  # Папка для сохранения файлов
THREADS = 10  # Количество потоков
LIMIT = 99999999999999999  # Сколько файлов скачать (99999999999999999 = все)

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

# Функция скачивания с прогрессом
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

        total_size = int(response.headers.get("content-length", 0))  # Получаем размер файла
        progress_bar = tqdm(total=total_size, unit="B", unit_scale=True, desc=name)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
                progress_bar.update(len(chunk))  # Обновляем прогресс

        progress_bar.close()
        print(f"✔ {name} скачан.")
    except requests.RequestException as e:
        print(f"❌ Ошибка скачивания {name}: {e}")

# Запускаем многопоточное скачивание с общим прогрессом
def download_all_files():
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        total_files = len(links)
        overall_progress = tqdm(total=total_files, desc="Общий прогресс", position=0)

        # Функция для отслеживания общего прогресса
        def on_done(future):
            overall_progress.update(1)

        for url, name in links:
            future = executor.submit(download_file, url, name)
            future.add_done_callback(on_done)
            futures.append(future)

        # Ожидаем завершения всех задач
        for future in futures:
            future.result()

        overall_progress.close()
        print("✅ Загрузка завершена!")

# Запуск процесса скачивания
download_all_files()
