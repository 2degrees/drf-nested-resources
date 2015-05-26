from django.db.models.base import Model
from django.db.models.fields import CharField


class Developer(Model):
    name = CharField()
