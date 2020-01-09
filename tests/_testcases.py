from django.db.models import Max
from django.test.testcases import TestCase as DjangoTestCase
from django.urls import set_urlconf

from django_project.languages.models import Developer
from django_project.languages.models import ProgrammingLanguage
from django_project.languages.models import ProgrammingLanguageVersion
from django_project.languages.models import Website
from django_project.languages.models import WebsiteHost


class TestCase(DjangoTestCase):

    def tearDown(self):
        # Ensure that any changes to the root URL config are reverted after the
        # test
        set_urlconf(None)
        super(TestCase, self).tearDown()


class FixtureTestCase(TestCase):

    def setUp(self):
        super(FixtureTestCase, self).setUp()

        self.developer1 = Developer.objects.create(name='Guido Rossum')
        self.developer2 = Developer.objects.create(name='Larry Wall')
        self.programming_language1 = ProgrammingLanguage.objects.create(
            name='Python',
            author=self.developer1,
        )
        self.programming_language2 = ProgrammingLanguage.objects.create(
            name='Perl',
            author=self.developer2,
        )
        self.programming_language_version = ProgrammingLanguageVersion.objects \
            .create(name='2.7', language=self.programming_language1)

        self.website = Website.objects.create(base_url='http://python.org/')
        self.programming_language1.website = self.website
        self.programming_language1.save()

        self.website_host = WebsiteHost.objects.create(name='AWS')
        self.website.hosts.add(self.website_host)

        self.non_existing_developer_pk = \
            Developer.objects.all().aggregate(Max('pk'))['pk__max'] + 1
