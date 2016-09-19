from functools import partial

from nose.tools import assert_is_none, assert_in
from nose.tools import eq_
from rest_framework.relations import PKOnlyObject
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory
from rest_framework.utils.model_meta import get_field_info

from drf_nested_resources.fields import HyperlinkedNestedIdentityField, \
    HyperlinkedNestedModelSerializer
from drf_nested_resources.fields import HyperlinkedNestedRelatedField
from drf_nested_resources.routers import NestedResource
from drf_nested_resources.routers import Resource
from drf_nested_resources.routers import make_urlpatterns_from_resources
from tests._testcases import FixtureTestCase
from tests._testcases import TestCase
from tests.django_project.app.models import ProgrammingLanguageVersion, \
    Developer, ProgrammingLanguage
from tests.django_project.app.views import DeveloperViewSet
from tests.django_project.app.views import ProgrammingLanguageVersionViewSet
from tests.django_project.app.views import ProgrammingLanguageViewSet


class TestIdentityField(TestCase):

    _SOURCE_VIEW_NAME = 'children'

    _DESTINATION_VIEW_NAME = 'child'

    _URLVARS_BY_VIEW_NAME = \
        {'children': ('parent', ), 'child': ('parent', 'child')}

    def setUp(self):
        super(TestIdentityField, self).setUp()
        self._django_request = _make_django_request(
            self._SOURCE_VIEW_NAME,
            {'parent': 'foo'},
            'tests.django_project.urls',
        )

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
        field = HyperlinkedNestedIdentityField(
            self._SOURCE_VIEW_NAME,
            self._URLVARS_BY_VIEW_NAME,
            )
        url = field.get_url(
            object_,
            self._DESTINATION_VIEW_NAME,
            drf_request,
            format_,
            )
        return url

    def _make_url_with_kwargs(self, pk, format_=None):
        source_view_kwargs = self._django_request.resolver_match[2]
        destination_view_kwargs = dict(source_view_kwargs, child=pk)
        url_path = reverse(
            self._DESTINATION_VIEW_NAME,
            kwargs=destination_view_kwargs,
            format=format_,
            )
        url = self._django_request.build_absolute_uri(url_path)
        return url


class TestRelatedLinkedField(FixtureTestCase):

    _URLVARS_BY_VIEW_NAME = {
        'developer-list': (),
        'developer-detail': ('developer',),
        'language-list': ('developer',),
        'language-detail': ('language', 'developer'),
        'version-list': ('language', 'developer'),
        'version-detail': ('version', 'language', 'developer'),
        }

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

    def test_parent_detail(self):
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

    def test_parent_list(self):
        source_view_name = 'language-detail'
        destination_view_name = 'developer-list'

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
            {},
            )
        eq_(expected_url, url)

    def test_grandparent_detail(self):
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

    def test_grandparent_list(self):
        source_view_name = 'version-detail'
        destination_view_name = 'developer-list'

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
            {},
            )
        eq_(expected_url, url)

    def test_child_detail(self):
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

    def test_child_list(self):
        source_view_name = 'language-detail'
        destination_view_name = 'version-list'

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

        field = HyperlinkedNestedRelatedField(
            source_view_name,
            self._URLVARS_BY_VIEW_NAME,
            read_only=True,
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


class TestSerializerURLFieldGeneration(FixtureTestCase):

    _RESOURCES = [
        Resource(
            'developer',
            'developers',
            DeveloperViewSet,
            [
                NestedResource(
                    'language',
                    'languages',
                    ProgrammingLanguageViewSet,
                    parent_field_lookup='author',
                ),
            ],
        ),
    ]

    def test_identity_field(self):
        serializer = _DeveloperSerializer(instance=self.developer1)
        field_class, field_kwargs = serializer.build_url_field('url', Developer)

        eq_(HyperlinkedNestedIdentityField, field_class)

        assert_in('view_name', field_kwargs)
        eq_('developer-detail', field_kwargs['view_name'])
        assert_in('urlvars_by_view_name', field_kwargs)
        eq_(
            _DeveloperSerializer.Meta.urlvars_by_view_name,
            field_kwargs['urlvars_by_view_name'],
        )

    def test_related_resource(self):
        serializer = \
            _ProgrammingLanguageSerializer(instance=self.programming_language1)

        field_info = get_field_info(ProgrammingLanguage)
        relation_info = field_info.forward_relations['author']
        field_class, field_kwargs = \
            serializer.build_relational_field('author', relation_info)

        eq_(HyperlinkedNestedRelatedField, field_class)

        assert_in('view_name', field_kwargs)
        eq_('developer-detail', field_kwargs['view_name'])
        assert_in('urlvars_by_view_name', field_kwargs)
        eq_(
            serializer.Meta.urlvars_by_view_name,
            field_kwargs['urlvars_by_view_name'],
        )

    def test_related_resource_collection(self):
        serializer = _DeveloperSerializer(instance=self.developer1)

        field_info = get_field_info(Developer)
        relation_info = field_info.reverse_relations['programming_languages']
        field_class, field_kwargs = serializer.build_relational_field(
            'programming_languages',
            relation_info,
        )

        eq_(HyperlinkedNestedRelatedField, field_class)

        assert_in('view_name', field_kwargs)
        eq_('language-list', field_kwargs['view_name'])
        assert_in('urlvars_by_view_name', field_kwargs)
        eq_(
            serializer.Meta.urlvars_by_view_name,
            field_kwargs['urlvars_by_view_name'],
        )


class _DeveloperSerializer(HyperlinkedNestedModelSerializer):

    class Meta:
        resource_name = 'developer'
        urlvars_by_view_name = {'developer': []}
        view_names_by_relationship = {'programming_languages': 'language'}


class _ProgrammingLanguageSerializer(HyperlinkedNestedModelSerializer):

    class Meta:
        resource_name = 'language'
        urlvars_by_view_name = {'language': []}
        view_names_by_relationship = {'author': 'developer'}


def _make_django_request(view_name, view_kwargs, urlconf=None):
    request_factory = APIRequestFactory(SERVER_NAME='example.org')
    url_path = reverse(view_name, kwargs=view_kwargs, urlconf=urlconf)
    django_request = request_factory.get(url_path)
    django_request.resolver_match = (view_name, (), view_kwargs)
    return django_request


def _make_drf_request(django_request):
    view_kwargs = django_request.resolver_match[2]
    drf_request = \
        Request(django_request, parser_context={'kwargs': view_kwargs})
    return drf_request
