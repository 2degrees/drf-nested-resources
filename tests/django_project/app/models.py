from django.db.models.base import Model
from django.db.models.fields import CharField
from django.db.models.fields import DateTimeField
from django.db.models.fields import URLField
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.related import OneToOneField


class Developer(Model):

    name = CharField(max_length=20)


class ProgrammingLanguage(Model):

    name = CharField(max_length=20)

    author = ForeignKey(Developer, related_name='programming_languages')

    website = \
        OneToOneField('Website', null=True, blank=True, related_name='language')


class ProgrammingLanguageVersion(Model):

    name = CharField(max_length=10)

    language = ForeignKey(ProgrammingLanguage, related_name='versions')


class ProgrammingLanguageImplementation(Model):

    name = CharField(max_length=10)

    language = ForeignKey(ProgrammingLanguage, related_name='implementations')


class Website(Model):

    base_url = URLField()

    hosts = ManyToManyField('WebsiteHost', related_name='websites')


class WebsiteVisit(Model):

    timestamp = DateTimeField(auto_now_add=True)

    website = ForeignKey(Website, related_name='visits')


class WebsiteHost(Model):

    name = CharField(max_length=50)
