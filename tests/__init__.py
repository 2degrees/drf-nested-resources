import os
import sys

from django import setup as dj_setup
from django.test.utils import setup_databases

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.extend([
    os.path.join(BASE_DIR, 'tests'),
])

os.environ['DJANGO_SETTINGS_MODULE'] = 'django_project.project.settings'


def setup():
    setup_databases(0, False)


dj_setup()
