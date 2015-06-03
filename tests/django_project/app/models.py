from django.db.models.base import Model
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey


class Developer(Model):
    name = CharField(max_length=20)


class ProgrammingLanguage(Model):

    name = CharField(max_length=20)

    author = ForeignKey(Developer, related_name='programming_languages')


class ProgrammingLanguageVersion(Model):

    name = CharField(max_length=10)

    language = ForeignKey(ProgrammingLanguage, related_name='versions')
