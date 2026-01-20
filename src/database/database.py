# database.py — обязательный файл для работы отчётов
import mysql.connector


def get_connection():
    """Единое подключение к БД — используется и в main.py, и в отчётах"""
    try:
        return mysql.connector.connect(
            host='pma.morohin.info',
            user='phpmyadmin',
            password='0907',
            database='phpmyadmin',   # ты уже переименовал — оставляем так
            charset='utf8mb4',
            autocommit=True
        )
    except Exception as e:
        print(f"Не удалось подключиться к БД: {e}")
        return None
