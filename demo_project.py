#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
sys.dont_write_bytecode = True
MISSING_DEPENDENCY = False
try:
    from django.conf import settings
except ImportError:
    sys.stdout.write("You'll need to `pip install Django` to run this demo\n")
    MISSING_DEPENDENCY = True

if MISSING_DEPENDENCY:
    sys.exit(1)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

