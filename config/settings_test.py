"""Settings exclusivos de CI/local; nunca leen .env ni heredan DATABASE_URL."""
import os
from unittest.mock import patch

# Solo se permite variar el puerto del PostgreSQL local dedicado.
_test_port = int(os.environ.get("TEST_POSTGRES_PORT", "55432"))
with patch.dict(os.environ, {
    "PYTHON_DOTENV_DISABLED": "1",
    "SECRET_KEY": "eventger-isolated-test-key-not-for-production",
}, clear=True):
    from .settings import *  # noqa: F403

DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "HOST": "127.0.0.1",
    "PORT": _test_port,
    "NAME": "eventger_ci",
    "USER": "eventger_ci",
    "PASSWORD": "eventger_ci_only",
    "OPTIONS": {"sslmode": "disable", "connect_timeout": 5},
    "TEST": {"NAME": "test_eventger_ci"},
}}
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
TEST_RUNNER = "ci.runner.NonEmptyXMLRunner"
TEST_OUTPUT_DIR = "reports"
