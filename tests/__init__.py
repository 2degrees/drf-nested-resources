from os import environ

from django import setup as dj_setup
from django.test.runner import setup_databases


environ['DJANGO_SETTINGS_MODULE'] = 'tests.django_project.settings'


def setup():
    dj_setup()
    setup_databases(0, False)
