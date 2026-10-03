"""本地 pytest 配置：以 sqlite 内存库跑 Django 测试，生产环境仍使用 PostgreSQL。

只在测试进程生效：django.setup() 之前替换 DATABASES，运行时配置（settings.py /
docker-compose）保持 PostgreSQL 不变。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.conf import settings as _settings_module  # noqa: E402

_settings_module.DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

import django  # noqa: E402
from django.test.runner import DiscoverRunner  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

django.setup()

setup_test_environment()
_runner = DiscoverRunner(verbosity=0)
_db_config = _runner.setup_databases()


def pytest_unconfigure(config):
    _runner.teardown_databases(_db_config)
    from django.test.utils import teardown_test_environment

    teardown_test_environment()
