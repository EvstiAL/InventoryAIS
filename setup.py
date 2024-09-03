import os
import subprocess

# Название вашего Flask приложения
app_name = "main.py"  # Замените на имя вашего файла приложения
output_dir = "dist"
additional_data = [
    ("templates", "templates"),  # Добавьте папку с шаблонами
    ("static", "static")         # Добавьте папку со статическими файлами
]

# Формируем команду для PyInstaller
command = ["pyinstaller", "--onefile", app_name]

# Добавляем дополнительные файлы
for src, dest in additional_data:
    command.append(f"--add-data={src};{dest}")

# Запускаем команду
subprocess.run(command)

# Проверяем, создан ли исполняемый файл
if os.path.exists(os.path.join(output_dir, os.path.basename(app_name).replace('.py', '.exe'))):
    print("Упаковка завершена успешно!")
else:
    print("Произошла ошибка при упаковке.")