"""让 pytest 直接可跑：配置 Django 设置模块。"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
