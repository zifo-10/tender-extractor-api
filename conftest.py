"""
Pytest root conftest.

Django settings are loaded via pytest.ini:
  DJANGO_SETTINGS_MODULE = config.settings.test
"""
import pytest


@pytest.fixture(autouse=False)
def db_access_without_rollback_and_truncate(db):
    """Convenience fixture alias."""
    pass
