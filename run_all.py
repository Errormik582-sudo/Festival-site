"""Запуск всего проекта одной командой."""
import subprocess
import sys
import os


def run(cmd, desc):
    """Запускает команду и падает, если она вернула не 0."""
    print(f'\n>>> {desc}')
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f'[ОШИБКА] Команда упала: {cmd}')
        sys.exit(1)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    run('python -m pip install -r requirements.txt', 'Установка зависимостей')
    run('python manage.py makemigrations', 'Создание миграций')
    run('python manage.py migrate', 'Применение миграций')
    run('python core/seed.py', 'Заполнение тестовыми данными')
    run('python manage.py runserver 0.0.0.0:8000', 'Запуск сервера')