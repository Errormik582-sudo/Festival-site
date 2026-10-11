"""
Конфигурация приложения core.

Django при старте ищет этот файл в каждом приложении из INSTALLED_APPS.
name = 'core' — обязательное поле, иначе Django не поймёт, что это за приложение.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'                       # Имя приложения (папка).
    verbose_name = 'Фестиваль'          # Как показывать в админке.