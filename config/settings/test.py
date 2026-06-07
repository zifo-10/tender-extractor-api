"""
Test-specific Django settings — uses SQLite in-memory to avoid PostgreSQL dependency.
"""
from .base import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Speed up password hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Disable throttling in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405

# Disable Slack in tests
SLACK_WEBHOOK_URL = ""

# Use dummy keys in tests
GROQ_API_KEY = "test-groq-key"
OPENAI_API_KEY = "test-openai-key"

# Disable logging noise in tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"]},
}
