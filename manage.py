#!/usr/bin/env python
import os
import sys

import sqlite_patch          # ← ПЕРВЫМ ДЕЛОМ, до импорта Django


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'festival_map.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django не установлен. Выполните: "
            "python -m pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()