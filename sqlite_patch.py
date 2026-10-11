# sqlite_patch.py
"""
Заменяем стандартный модуль sqlite3 на pysqlite3.

Стандартный модуль в этом Python собран без поддержки расширений,
поэтому GeoDjango не может загрузить SpatiaLite. pysqlite3-binary —
это та же библиотека, но собранная с нужным флагом.
"""
import sys
import pysqlite3

# Подменяем модуль в sys.modules. После этого любой `import sqlite3`
# в программе получит pysqlite3.
sys.modules['sqlite3'] = pysqlite3