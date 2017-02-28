#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
sys.dont_write_bytecode = True
MISSING_DEPENDENCIES = []
try:
    from django.conf import settings
except ImportError:
    MISSING_DEPENDENCIES.append("Django")
try:
    import intercoolerjs
except ImportError:
    MISSING_DEPENDENCIES.append("django-intercoolerjs")

if MISSING_DEPENDENCIES:
    deps = " ".join(MISSING_DEPENDENCIES)
    sys.stdout.write("You'll need to `pip install {}` to run this demo\n".format(deps))
    sys.exit(1)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

