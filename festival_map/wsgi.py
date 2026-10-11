"""
WSGI-конфигурация.

Этот файл нужен Django для запуска через WSGI-серверы (gunicorn, uwsgi)
в продакшене. При разработке (runserver) он тоже подгружается.
Без него Django 5.x может ругаться на отсутствие модуля.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'festival_map.settings')

application = get_wsgi_application()