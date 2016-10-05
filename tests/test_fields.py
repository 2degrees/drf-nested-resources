from abc import ABCMeta, abstractproperty

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import resolve
from nose.tools import assert_is_none, assert_in
from nose.tools import assert_raises
from nose.tools import eq_
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory
from rest_framework.utils.model_meta import get_field_info

from drf_nested_resources.fields import HyperlinkedNestedIdentityField
from drf_nested_resources.fields import HyperlinkedNestedRelatedField
from drf_nested_resources.lookup_helpers import RequestParentLookupHelper
from drf_nested_resources.routers import NestedResource
from drf_nested_resources.routers import Resource
from drf_nested_resources.routers import make_urlpatterns_from_resources

from tests._testcases import FixtureTestCase
from tests.django_project.app.models import Developer, ProgrammingLanguage, \
    Website
from tests.django_project.app.views import DeveloperViewSet, DeveloperViewSet2, \
    WebsiteHostViewSet, WebsiteViewSet, WebsiteVisitViewSet
from tests.django_project.app.views import ProgrammingLanguageVersionViewSet
from tests.django_project.app.views import ProgrammingLanguageViewSet


_REQUEST_FACTORY = APIRequestFactory(SERVER_NAME='example.org')


class _BaseTestCase(FixtureTestCase):

    def __init__(self, *args, **kwargs):
        super(_BaseTestCase, self).__init__(*args, **kwargs)
        self.resources = None
        self.urlpatterns = None

    def setUp(self):
        super(_BaseTestCase, self).setUp()

        website_resource = Resource('website', 'websites', WebsiteViewSet)
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
                        cross_linked_resources={'website': website_resource},
                    ),
                ],

            ),
            Resource(
                'website-visit',
                'website-visits',
                WebsiteVisitViewSet,
                cross_linked_resources={'website': website_resource},
            ),
            website_resource,
        ]

        self.urlpatterns = make_urlpatterns_from_resources(self.resources)

    @staticmethod
    def _get_serializer_by_name(
        drf_request,
        urlpatterns,
        view_name,
        view_kwargs=None,
        format_=None,
    ):
        url = reverse(view_name, kwargs=view_kwargs, urlconf=urlpatterns)
        view_func = resolve(url, urlpatterns).func
        viewset = view_func.cls(
            request=drf_request,
            format_kwarg=format_,
            **view_func.initkwargs,
        )
        serializer = viewset.get_serializer()
        return serializer

    @staticmethod
    def _make_django_request(view_name, view_kwargs, urlpatterns):
        url_path = \
            reverse(view_name, kwargs=view_kwargs, urlconf=urlpatterns)
        django_request = _REQUEST_FACTORY.get(url_path)
        django_request.resolver_match = (view_name, (), view_kwargs)
        django_request.urlconf = urlpatterns
        return django_request

    @staticmethod
    def _make_drf_request(django_request):
        view_kwargs = django_request.resolver_match[2]
        drf_request = \
            Request(django_request, parser_context={'kwargs': view_kwargs})
        return drf_request


class _BaseHyperlinkedFieldTestCase(_BaseTestCase, metaclass=ABCMeta):

    FIELD_CLASS = abstractproperty()

    def _make_url_via_field(
        self,
        destination_view_name,
        destination_view_object,
        source_view_name='developer-list',
        source_view_kwargs=None,
        urlpatterns=None,
        format_=None,
    ):
        urlpatterns = urlpatterns or self.urlpatterns

        django_request = self._make_django_request(
            source_view_name,
            source_view_kwargs or {},
            urlpatterns,
        )
        drf_request = self._make_drf_request(django_request)

        url_generator = \
            self._get_url_generator(drf_request, urlpatterns, format_)
        field = self.FIELD_CLASS(
            source_view_name,
            url_generator=url_generator,
            read_only=True,
        )

        url = field.get_url(
            destination_view_object,
            destination_view_name,
            drf_request,
            format_,
        )
        return url

    def _get_url_generator(self, drf_request, urlpatterns, format_):
        serializer = self._get_serializer_by_name(
            drf_request,
            urlpatterns,
            'developer-list',
            format_=format_,
        )
        url_generator = serializer.Meta.url_generator
        return url_generator

    def _make_url_with_kwargs(
        self,
        view_name,
        view_kwargs,
        urlpatterns=None,
        format_=None,
    ):
        django_request = _REQUEST_FACTORY.get('/')
        url_path = reverse(
            view_name,
            kwargs=view_kwargs,
            urlconf=urlpatterns or self.urlpatterns,
            format=format_,
        )
        url = django_request.build_absolute_uri(url_path)
        return url


class TestIdentityField(_BaseHyperlinkedFieldTestCase):

    FIELD_CLASS = HyperlinkedNestedIdentityField

    VIEW_NAME = 'developer-detail'

    def test_url_generation(self):
        url = self._make_url_via_field(self.VIEW_NAME, self.developer1)
        expected_url = self._make_url_with_kwargs(self.developer1)
        eq_(expected_url, url)

    def test_url_generation_with_explicit_format(self):
        url = self._make_url_via_field(
            self.VIEW_NAME,
            self.developer1,
            format_='xml',
        )
        expected_url = self._make_url_with_kwargs(self.developer1, 'xml')
        eq_(expected_url, url)

    def test_unsaved_resource(self):
        url = self._make_url_via_field(self.VIEW_NAME, Developer())
        assert_is_none(url)

    def _make_url_with_kwargs(self, object_, format_=None):
        url = super(TestIdentityField, self)._make_url_with_kwargs(
            self.VIEW_NAME,
            {'developer': object_.pk},
            format_=format_,
        )
        return url


class TestRelatedLinkedFieldURLGeneration(_BaseHyperlinkedFieldTestCase):

    FIELD_CLASS = HyperlinkedNestedRelatedField

    def test_top_level_resource(self):
        view_name = 'developer-detail'
        url_generated = self._make_url_via_field(view_name, self.developer1)
        url_expected = self._make_url_with_kwargs(
            view_name,
            {'developer': self.developer1.pk},
        )
        eq_(url_expected, url_generated)

    def test_nested_collection(self):
        view_name = 'language-list'
        url_generated = self._make_url_via_field(
            view_name,
            self.developer1.programming_languages,
        )
        url_expected = self._make_url_with_kwargs(
            view_name,
            {'developer': self.developer1.pk},
        )
        eq_(url_expected, url_generated)

    def test_nested_resource(self):
        programming_language = self.programming_language1
        view_name = 'language-detail'
        url_generated = self._make_url_via_field(
            view_name,
            programming_language,
        )
        url_expected = self._make_url_with_kwargs(
            view_name,
            {
                'developer': programming_language.author.pk,
                'language': programming_language.pk,
            },
        )
        eq_(url_expected, url_generated)

    def test_sub_nested_collection(self):
        view_name = 'version-list'
        url_generated = self._make_url_via_field(
            view_name,
            self.programming_language1.versions,
        )
        url_expected = self._make_url_with_kwargs(
            view_name,
            {
                'developer': self.developer1.pk,
                'language': self.programming_language1.pk,
            },
        )
        eq_(url_expected, url_generated)

    def test_sub_nested_resource(self):
        version = self.programming_language_version
        view_name = 'version-detail'
        url_generated = self._make_url_via_field(view_name, version)
        url_expected = self._make_url_with_kwargs(
            view_name,
            {
                'developer': version.language.author.pk,
                'language': version.language.pk,
                'version': version.pk
            },
        )
        eq_(url_expected, url_generated)

    def test_unsaved_resource(self):
        view_name = 'developer-detail'
        url_generated = self._make_url_via_field(view_name, Developer())
        assert_is_none(url_generated)

    def test_format(self):
        view_name = 'developer-detail'
        format_ = 'json'
        url_generated = self._make_url_via_field(
            view_name,
            self.developer1,
            format_=format_,
        )
        url_expected = self._make_url_with_kwargs(
            view_name,
            {'developer': self.developer1.pk},
            format_=format_,
        )
        eq_(url_expected, url_generated)

    def test_indirect_model_relation_resource(self):
        resources = [
            Resource(
                'developer',
                'developers',
                DeveloperViewSet2,
                [
                    NestedResource(
                        'version',
                        'versions',
                        ProgrammingLanguageVersionViewSet,
                        parent_field_lookup='language__author',
                    ),
                ],
            ),
        ]
        urlpatterns = make_urlpatterns_from_resources(resources)

        version = self.programming_language_version
        view_name = 'version-detail'
        url_generated = self._make_url_via_field(
            view_name,
            version,
            urlpatterns=urlpatterns,
        )
        url_expected = self._make_url_with_kwargs(
            view_name,
            {
                'developer': self.developer1.pk,
                'version': version.pk,
            },
            urlpatterns=urlpatterns,
        )
        eq_(url_expected, url_generated)

    def test_unsupported_object(self):
        view_name = 'developer-detail'
        assert_raises(
            AssertionError,
            self._make_url_via_field,
            view_name,
            object(),
        )

    def test_illegal_view_type(self):
        view_name = 'developer-foo'
        assert_raises(
            AssertionError,
            self._make_url_via_field,
            view_name,
            self.developer1,
        )

    def test_illegal_field_type(self):
        resources = [
            Resource(
                'developer',
                'developers',
                DeveloperViewSet,
                [
                    NestedResource(
                        'language',
                        'languages',
                        ProgrammingLanguageViewSet,
                        parent_field_lookup=RequestParentLookupHelper(
                            'author', 'developer'),
                    ),
                ],
            ),
        ]

        urlpatterns = make_urlpatterns_from_resources(resources)

        assert_raises(
            AssertionError,
            self._make_url_via_field,
            'language-detail',
            self.programming_language1,
            source_view_name='developer-detail',
            source_view_kwargs={'developer': self.programming_language1.author},
            urlpatterns=urlpatterns,
        )

    def test_improperly_configured_related_field(self):
        resources = [
            Resource(
                'host',
                'hosts',
                WebsiteHostViewSet,
                [
                    NestedResource(
                        'website',
                        'websites',
                        WebsiteViewSet,
                        parent_field_lookup=RequestParentLookupHelper(
                            'hosts',
                            'host',
                        ),
                    ),
                ],
            ),
            Resource('developer', 'developers', DeveloperViewSet)
        ]
        urlpatterns = make_urlpatterns_from_resources(resources)

        assert_raises(
            ImproperlyConfigured,
            self._make_url_via_field,
            'website-detail',
            self.programming_language1,
            urlpatterns=urlpatterns,
        )

    def test_illegal_parent_field_lookup_type(self):
        resources = [
            Resource(
                'developer',
                'developers',
                DeveloperViewSet,
                [
                    NestedResource(
                        'language',
                        'languages',
                        ProgrammingLanguageViewSet,
                        parent_field_lookup=_FakeParentLookupHelper('author'),
                    ),
                ],
            ),
        ]

        urlpatterns = make_urlpatterns_from_resources(resources)

        assert_raises(
            AssertionError,
            self._make_url_via_field,
            'language-detail',
            self.programming_language1,
            urlpatterns=urlpatterns,
        )


class TestSerializerURLFieldGeneration(_BaseTestCase):

    def test_identity_field(self):
        serializer = self._get_serializer_for_view(
            'developer-detail',
            {'developer': self.developer1.pk},
        )
        field_class, field_kwargs = serializer.build_url_field('url', Developer)

        eq_(HyperlinkedNestedIdentityField, field_class)
        self._check_field_kwargs(field_kwargs, serializer, 'developer-detail')

    def test_related_resource(self):
        serializer = self._get_serializer_for_view(
            'language-detail',
            {
                'developer': self.programming_language1.author.pk,
                'language': self.programming_language1.pk,
            },
        )

        field_info = get_field_info(ProgrammingLanguage)
        relation_info = field_info.forward_relations['author']
        field_class, field_kwargs = \
            serializer.build_relational_field('author', relation_info)

        self._assert_field_is_related_field(field_class)
        self._check_field_kwargs(field_kwargs, serializer, 'developer-detail')
        self._check_lookup_url_kwarg_in_field_kwargs('developer', field_kwargs)

    def test_related_resource_collection(self):
        serializer = self._get_serializer_for_view(
            'developer-detail',
            {'developer': self.developer1.pk},
        )

        field_info = get_field_info(Developer)
        relation_info = field_info.reverse_relations['programming_languages']
        field_class, field_kwargs = serializer.build_relational_field(
            'programming_languages',
            relation_info,
        )

        self._assert_field_is_related_field(field_class)
        self._check_field_kwargs(field_kwargs, serializer, 'language-list')

    def test_related_resource_with_no_common_ancestor(self):
        serializer = self._get_serializer_for_view(
            'language-detail',
            {
                'developer': self.programming_language1.author.pk,
                'language': self.programming_language1.pk,
            },
        )

        field_info = get_field_info(ProgrammingLanguage)
        relation_info = field_info.forward_relations['website']
        field_class, field_kwargs = \
            serializer.build_relational_field('website', relation_info)

        self._assert_field_is_related_field(field_class)
        self._check_field_kwargs(field_kwargs, serializer, 'website-detail')
        self._check_lookup_url_kwarg_in_field_kwargs('website', field_kwargs)

    def test_related_resource_collection_with_no_common_ancestor(self):
        serializer = self._get_serializer_for_view(
            'website-detail',
            {'website': self.website.pk},
        )

        field_info = get_field_info(Website)
        relation_info = field_info.reverse_relations['visits']
        field_class, field_kwargs = serializer.build_relational_field(
            'visits',
            relation_info,
        )

        self._assert_field_is_related_field(field_class)
        self._check_field_kwargs(
            field_kwargs,
            serializer,
            'website_visit-list',
        )

    def _get_serializer_for_view(self, view_name, view_kwargs):
        django_request = \
            self._make_django_request('developer-list', None, self.urlpatterns)
        drf_request = self._make_drf_request(django_request)
        serializer = self._get_serializer_by_name(
            drf_request,
            self.urlpatterns,
            view_name,
            view_kwargs,
        )
        return serializer

    @staticmethod
    def _assert_field_is_related_field(field_class):
        eq_(HyperlinkedNestedRelatedField, field_class)

    @staticmethod
    def _check_field_kwargs(field_kwargs, serializer, expected_view_name):
        assert_in('view_name', field_kwargs)
        eq_(expected_view_name, field_kwargs['view_name'])
        assert_in('url_generator', field_kwargs)
        eq_(
            serializer.__class__.Meta.url_generator,
            field_kwargs['url_generator'],
        )

    @staticmethod
    def _check_lookup_url_kwarg_in_field_kwargs(
        expected_lookup_url_kwarg,
        field_kwargs,
    ):
        assert_in('lookup_url_kwarg', field_kwargs)
        eq_(expected_lookup_url_kwarg, field_kwargs['lookup_url_kwarg'])


class _FakeParentLookupHelper(object):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value
