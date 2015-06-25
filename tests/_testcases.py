from django.test.testcases import TransactionTestCase

from tests.django_project.app.models import Developer
from tests.django_project.app.models import WebsiteHost
from tests.django_project.app.models import Website
from tests.django_project.app.models import ProgrammingLanguage
from tests.django_project.app.models import ProgrammingLanguageVersion


class FixtureTestCase(TransactionTestCase):

    reset_sequences = True

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
