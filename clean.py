import os
import time
from apscheduler.schedulers.background import BackgroundScheduler

def clear_console():
    """Очищает консоль."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Консоль очищена.")

def start_console_cleanup_scheduler(interval_minutes=1):
    """Запускает планировщик для очистки консоли через указанный интервал."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(clear_console, 'interval', minutes=interval_minutes)  # Очищать консоль каждые N минут
    scheduler.start()
    print("Планировщик очистки консоли запущен.")
