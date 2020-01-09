from django.db.models import CASCADE
from django.db.models import SET_NULL
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

    author = ForeignKey(
        Developer,
        related_name='programming_languages',
        on_delete=CASCADE,
    )

    website = OneToOneField(
        'Website',
        null=True,
        blank=True,
        related_name='language',
        on_delete=SET_NULL,
    )


class ProgrammingLanguageVersion(Model):
    name = CharField(max_length=10)

    language = ForeignKey(
        ProgrammingLanguage,
        related_name='versions',
        on_delete=CASCADE,
    )


class ProgrammingLanguageImplementation(Model):
    name = CharField(max_length=10)

    language = ForeignKey(
        ProgrammingLanguage,
        related_name='implementations',
        on_delete=CASCADE,
    )


class Website(Model):
    base_url = URLField()

    hosts = ManyToManyField('WebsiteHost', related_name='websites')


class WebsiteVisit(Model):
    timestamp = DateTimeField(auto_now_add=True)

    website = ForeignKey(
        Website,
        related_name='visits',
        on_delete=CASCADE,
    )


class WebsiteHost(Model):
    name = CharField(max_length=50)
