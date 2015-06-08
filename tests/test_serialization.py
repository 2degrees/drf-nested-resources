from functools import partial

from nose.tools import assert_is_none
from nose.tools import eq_
from rest_framework.compat import RequestFactory
from rest_framework.relations import PKOnlyObject
from rest_framework.request import Request
from rest_framework.reverse import reverse

from drf_nested_resources.fields import HyperlinkedNestedIdentityField
from drf_nested_resources.fields import HyperlinkedNestedRelatedField
from drf_nested_resources.routers import NestedResource
from drf_nested_resources.routers import Resource
from drf_nested_resources.routers import _flatten_nested_resources
from drf_nested_resources.routers import make_urlpatterns_from_resources
from tests._testcases import FixtureTestCase
from tests.django_project.app.models import ProgrammingLanguageVersion
from tests.django_project.app.views import DeveloperViewSet
from tests.django_project.app.views import ProgrammingLanguageVersionViewSet
from tests.django_project.app.views import ProgrammingLanguageViewSet


class TestIdentityField(object):

    _SOURCE_VIEW_NAME = 'children'

    _DESTINATION_VIEW_NAME = 'child'

    def setup(self):
        self._django_request = \
            _make_django_request(self._SOURCE_VIEW_NAME, {'parent_id': 'foo'})

    def test_url_generation(self):
        url = self._make_url_with_kwargs_via_field('foo')
        expected_url = self._make_url_with_kwargs('foo')
        eq_(expected_url, url)

    def test_url_generation_with_explicit_format(self):
        url = self._make_url_with_kwargs_via_field('foo', 'xml')
        expected_url = self._make_url_with_kwargs('foo', 'xml')
        eq_(expected_url, url)

    def test_unsaved_resource(self):
        url = self._make_url_with_kwargs_via_field(None)
        assert_is_none(url)

    def _make_url_with_kwargs_via_field(self, pk, format_=None):
        object_ = PKOnlyObject(pk)
        drf_request = _make_drf_request(self._django_request)
        field = HyperlinkedNestedIdentityField(self._SOURCE_VIEW_NAME)
        url = field.get_url(
            object_,
            self._DESTINATION_VIEW_NAME,
            drf_request,
            format_,
            )
        return url

    def _make_url_with_kwargs(self, pk, format_=None):
        source_view_kwargs = self._django_request.resolver_match[2]
        destination_view_kwargs = dict(source_view_kwargs, pk=pk)
        if format_:
            destination_view_kwargs['format'] = format_
        url_path = \
            reverse(self._DESTINATION_VIEW_NAME, kwargs=destination_view_kwargs)
        url = self._django_request.build_absolute_uri(url_path)
        return url


class TestRelatedLinkedField(FixtureTestCase):

    def setUp(self):
        super(TestRelatedLinkedField, self).setUp()

        self.resources = [
            Resource(
                'developer',
                'developers',
                DeveloperViewSet,
                [
                    NestedResource(
                        'language',
                        'languages',
                        ProgrammingLanguageViewSet,
                        [
                            NestedResource(
                                'version',
                                'versions',
                                ProgrammingLanguageVersionViewSet,
                                parent_field_lookup='language',
                                ),
                            ],
                        parent_field_lookup='author',
                        ),
                    ],
                ),
            ]
        self.urlpatterns = make_urlpatterns_from_resources(self.resources)

    def test_parent(self):
        source_view_name = 'language-detail'
        destination_view_name = 'developer-detail'

        django_request = _make_django_request(
            source_view_name,
            {
                'developer': self.developer1.pk,
                'language': self.programming_language1.pk,
                },
            self.urlpatterns,
            )
        url = self._make_url_via_field(
            django_request,
            source_view_name,
            destination_view_name,
            self.developer1,
            )
        expected_url = self._make_url_with_kwargs(
            django_request,
            destination_view_name,
            {'developer': self.developer1.pk},
            )
        eq_(expected_url, url)

    def test_grandparent(self):
        source_view_name = 'version-detail'
        destination_view_name = 'developer-detail'

        django_request = _make_django_request(
            source_view_name,
            {
                'developer': self.developer1.pk,
                'language': self.programming_language1.pk,
                'version': self.programming_language_version.pk,
                },
            self.urlpatterns,
            )
        url = self._make_url_via_field(
            django_request,
            source_view_name,
            destination_view_name,
            self.developer1,
            )
        expected_url = self._make_url_with_kwargs(
            django_request,
            destination_view_name,
            {'developer': self.developer1.pk},
            )
        eq_(expected_url, url)

    def test_child(self):
        source_view_name = 'language-detail'
        destination_view_name = 'version-detail'

        django_request = _make_django_request(
            source_view_name,
            {
                'developer': self.developer1.pk,
                'language': self.programming_language1.pk,
                },
            self.urlpatterns,
            )

        url = self._make_url_via_field(
            django_request,
            source_view_name,
            destination_view_name,
            self.programming_language_version,
            )
        expected_url = self._make_url_with_kwargs(
            django_request,
            destination_view_name,
            {
                'developer': self.developer1.pk,
                'language': self.programming_language1.pk,
                'version': self.programming_language_version.pk,
                },
            )
        eq_(expected_url, url)


    def test_unsaved_child(self):
        source_view_name = 'language-detail'
        destination_view_name = 'version-detail'

        django_request = _make_django_request(
            source_view_name,
            {
                'developer': self.developer1.pk,
                'language': self.programming_language1.pk,
                },
            self.urlpatterns,
            )

        url = self._make_url_via_field(
            django_request,
            source_view_name,
            destination_view_name,
            ProgrammingLanguageVersion(language=self.programming_language1),
            )
        assert_is_none(url)

    def _make_url_via_field(
        self,
        django_request,
        source_view_name,
        destination_view_name,
        destination_view_object,
        ):
        drf_request = _make_drf_request(django_request)

        urlvars_by_resource_name = {
            'version': ('version', 'language', 'developer'),
            'language': ('language', 'developer'),
            'developer': ('developer',),
            }

        field = HyperlinkedNestedRelatedField(
            source_view_name,
            read_only=True,
            urlvars_by_resource_name=urlvars_by_resource_name,
            )
        field.reverse = partial(reverse, urlconf=self.urlpatterns)

        url = field.get_url(
            destination_view_object,
            destination_view_name,
            drf_request,
            None,
            )
        return url

    def _make_url_with_kwargs(self, django_request, view_name, view_kwargs):
        url_path = \
            reverse(view_name, kwargs=view_kwargs, urlconf=self.urlpatterns)
        url = django_request.build_absolute_uri(url_path)
        return url


def _make_django_request(view_name, view_kwargs, urlconf=None):
    request_factory = RequestFactory()
    url_path = reverse(view_name, kwargs=view_kwargs, urlconf=urlconf)
    django_request = request_factory.get(url_path)
    django_request.resolver_match = (view_name, (), view_kwargs)
    return django_request


def _make_drf_request(django_request):
    view_kwargs = django_request.resolver_match[2]
    drf_request = \
        Request(django_request, parser_context={'kwargs': view_kwargs})
    return drf_request
