# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

def pytest_configure():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")
    import django
    from django.conf import settings
    if settings.configured and hasattr(django, 'setup'):
        django.setup()
