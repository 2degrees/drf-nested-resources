from django.conf.urls import include
from django.conf.urls import url
from django.core.urlresolvers import resolve
from nose.tools import assert_raises
from nose.tools import eq_
from nose.tools import ok_
from rest_framework.reverse import reverse
from rest_framework.routers import SimpleRouter
from rest_framework.test import APIRequestFactory
from rest_framework.versioning import NamespaceVersioning

from drf_nested_resources.lookup_helpers import RequestParentLookupHelper
from drf_nested_resources.routers import NestedResource
from drf_nested_resources.routers import Resource
from drf_nested_resources.routers import make_urlpatterns_from_resources
from tests._testcases import FixtureTestCase
from tests._testcases import TestCase
from tests._utils import TestClient, make_response_for_request
from tests.django_project.app.models import Website
from tests.django_project.app.models import WebsiteVisit
from tests.django_project.app.views import DeveloperViewSet
from tests.django_project.app.views import DeveloperViewSet2
from tests.django_project.app.views import ProgrammingLanguageVersionViewSet
from tests.django_project.app.views import ProgrammingLanguageViewSet
from tests.django_project.app.views import WebsiteHostViewSet
from tests.django_project.app.views import WebsiteViewSet
from tests.django_project.app.views import WebsiteVisitViewSet


class TestURLPatternGeneration(TestCase):
    @staticmethod
    def test_default_router():
        resources = []
        urlpatterns = make_urlpatterns_from_resources(resources)
        eq_(2, len(urlpatterns))

        url_path1 = reverse('api-root', urlconf=urlpatterns)
        eq_('/', url_path1)

        url_path2 = \
            reverse('api-root', kwargs={'format': 'json'}, urlconf=urlpatterns)
        eq_('/.json', url_path2)

    @staticmethod
    def test_resources_resolution_with_default_router():
        resources = [Resource('developer', 'developers', DeveloperViewSet)]
        urlpatterns = make_urlpatterns_from_resources(resources)

        url_path = reverse('developer-list', urlconf=urlpatterns)
        eq_('/developers/', url_path)

        view_callable, view_args, view_kwargs = resolve(url_path, urlpatterns)
        ok_(getattr(view_callable, 'is_fixture', False))
        eq_((), view_args)
        eq_({}, view_kwargs)

    @staticmethod
    def test_resources_resolution_with_custom_router():
        resources = [Resource('developer', 'developers', DeveloperViewSet)]
        urlpatterns = make_urlpatterns_from_resources(resources, SimpleRouter)
        eq_(2, len(urlpatterns))

        url_path1 = reverse('developer-list', urlconf=urlpatterns)
        eq_('/developers/', url_path1)

        url_path2 = reverse(
            'developer-detail',
            kwargs={'developer': 1},
            urlconf=urlpatterns,
        )
        eq_('/developers/1/', url_path2)

    @staticmethod
    def test_resources_resolution_with_hyphenated_resource_name():
        resources = \
            [Resource('software-developer', 'developers', DeveloperViewSet)]
        urlpatterns = make_urlpatterns_from_resources(resources)

        url_path1 = reverse('software_developer-list', urlconf=urlpatterns)
        eq_('/developers/', url_path1)

        url_path2 = reverse(
            'software_developer-detail',
            kwargs={'software_developer': 1},
            urlconf=urlpatterns,
        )
        eq_('/developers/1/', url_path2)

    @staticmethod
    def test_resources_resolution_with_invalid_resource_name():
        resources = [Resource('2015developer', 'developers', DeveloperViewSet)]
        with assert_raises(AssertionError):
            make_urlpatterns_from_resources(resources)

    @staticmethod
    def test_nested_resources_resolution():
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
                        parent_field_lookup='author',
                    ),
                ],
            ),
        ]
        urlpatterns = make_urlpatterns_from_resources(resources)

        url_path = reverse(
            'language-list',
            kwargs={'developer': 1},
            urlconf=urlpatterns,
        )
        eq_('/developers/1/languages/', url_path)


class TestDispatch(FixtureTestCase):
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
                    [
                        NestedResource(
                            'visit',
                            'visits',
                            WebsiteVisitViewSet,
                            parent_field_lookup='website__language',
                        ),
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

    def test_parent_detail(self):
        response = self._make_response_for_request(
            'developer-detail',
            {'developer': self.developer1.pk},
        )

        response_data = response.data

        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)
        expected_languages_url = reverse(
            'language-list',
            kwargs={'developer': self.developer1.pk},
            urlconf=urlpatterns,
        )
        languages_url = response_data['programming_languages']
        ok_(languages_url.endswith(expected_languages_url))

        eq_(200, response.status_code)

    def test_parent_list(self):
        response = self._make_response_for_request('developer-list')
        eq_(200, response.status_code)

    def test_parent_list_mounted_on_different_url_path(self):
        api_urls = list(make_urlpatterns_from_resources(self._RESOURCES))
        urlpatterns = (url(r'^api/', include(api_urls)),)

        client = TestClient(urlpatterns)

        url_path = reverse('developer-list', urlconf=urlpatterns)
        response = client.get(url_path)
        eq_(200, response.status_code)

    def test_non_existing_parent_detail(self):
        response = self._make_response_for_request(
            'developer-detail',
            {'developer': self.non_existing_developer_pk},
        )
        eq_(404, response.status_code)

    def test_child_detail(self):
        view_kwargs = {
            'developer': self.developer1.pk,
            'language': self.programming_language1.pk,
        }
        response = \
            self._make_response_for_request('language-detail', view_kwargs)
        eq_(200, response.status_code)

    def test_child_detail_inside_namespace(self):
        namespace = 'v1'

        api_urls = make_urlpatterns_from_resources(self._RESOURCES)
        urlpatterns = _mount_urls_on_namespace(api_urls, namespace)

        response = _make_request_to_namespaced_url(
            namespace,
            'language-detail',
            {
                'developer': self.developer1.pk,
                'language': self.programming_language1.pk,
            },
            urlpatterns,
        )
        eq_(200, response.status_code)

    def test_child_list(self):
        response = self._make_response_for_request(
            'language-list',
            {'developer': self.developer1.pk},
        )
        eq_(200, response.status_code)

    def test_child_detail_with_wrong_parent(self):
        view_kwargs = {
            'developer': self.developer1.pk,
            'language': self.programming_language2.pk,
        }
        response = \
            self._make_response_for_request('language-detail', view_kwargs)
        eq_(404, response.status_code)

    def test_child_detail_with_non_existing_parent(self):
        view_kwargs = {
            'developer': self.non_existing_developer_pk,
            'language': self.programming_language1.pk,
        }
        response = \
            self._make_response_for_request('language-detail', view_kwargs)
        eq_(404, response.status_code)

    def test_child_list_with_non_existing_parent(self):
        response = self._make_response_for_request(
            'language-list',
            {'developer': self.non_existing_developer_pk},
        )
        eq_(404, response.status_code)

    def test_child_detail_with_non_viewable_parent(self):
        resources = [
            Resource(
                'website',
                'websites',
                _WebsiteViewSetWithCustomGetQueryset,
                [
                    NestedResource(
                        'host',
                        'hosts',
                        WebsiteHostViewSet,
                        parent_field_lookup='websites',
                    ),
                ],
            ),
        ]

        view_kwargs = {
            'website': self.website.pk,
            'host': self.website_host.pk,
        }
        response = \
            make_response_for_request('host-detail', view_kwargs, resources)
        eq_(404, response.status_code)

    def test_child_list_with_non_viewable_parent(self):
        resources = [
            Resource(
                'website',
                'websites',
                _WebsiteViewSetWithCustomGetQueryset,
                [
                    NestedResource(
                        'host',
                        'hosts',
                        WebsiteHostViewSet,
                        parent_field_lookup='websites',
                    ),
                ],
            ),
        ]

        response = make_response_for_request(
            'host-list',
            {'website': self.website.pk},
            resources,
        )
        eq_(404, response.status_code)

    def test_non_existing_child_detail(self):
        view_kwargs = {
            'developer': self.developer1.pk,
            'language': self.non_existing_developer_pk,
        }
        response = \
            self._make_response_for_request('language-detail', view_kwargs)
        eq_(404, response.status_code)

    def test_grand_child_detail(self):
        view_kwargs = {
            'developer': self.developer1.pk,
            'language': self.programming_language1.pk,
            'version': self.programming_language_version.pk,
        }
        response = \
            self._make_response_for_request('version-detail', view_kwargs)
        eq_(200, response.status_code)

    def test_detail_with_non_existing_grandparent(self):
        view_kwargs = {
            'developer': self.non_existing_developer_pk,
            'language': self.programming_language1.pk,
            'version': self.programming_language_version.pk,
        }
        response = \
            self._make_response_for_request('version-detail', view_kwargs)
        eq_(404, response.status_code)

    def test_indirect_relation_detail(self):
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
        view_kwargs = {
            'developer': self.developer1.pk,
            'version': self.programming_language_version.pk,
        }
        response = \
            make_response_for_request('version-detail', view_kwargs, resources)
        eq_(200, response.status_code)

    def test_indirect_child_detail_via_one_to_one(self):
        visit = WebsiteVisit.objects.create(website=self.website)
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
                        [
                            NestedResource(
                                'visit',
                                'visits',
                                WebsiteVisitViewSet,
                                parent_field_lookup='website__language',
                            ),
                        ],
                        parent_field_lookup='author',
                    ),
                ],
            ),
        ]
        view_kwargs = {
            'developer': self.developer1.pk,
            'language': self.programming_language1.pk,
            'visit': visit.pk,
        }
        response = \
            make_response_for_request('visit-detail', view_kwargs, resources)
        eq_(200, response.status_code)

    def test_many_to_many_relationships(self):
        resources = [
            Resource(
                'website',
                'websites',
                WebsiteViewSet,
                [
                    NestedResource(
                        'host',
                        'hosts',
                        WebsiteHostViewSet,
                        parent_field_lookup=RequestParentLookupHelper(
                            'websites',
                            'website',
                        ),
                    ),
                ],
            ),
        ]
        view_kwargs = {
            'website': self.website.pk,
            'host': self.website_host.pk,
        }
        response = \
            make_response_for_request('host-detail', view_kwargs, resources)
        eq_(200, response.status_code)

    def test_reverse_many_to_many_relationships(self):
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
        ]
        view_kwargs = {
            'website': self.website.pk,
            'host': self.website_host.pk,
        }
        response = \
            make_response_for_request('website-detail', view_kwargs, resources)
        eq_(200, response.status_code)

    def _make_response_for_request(self, view_name, view_kwargs=None):
        response = \
            make_response_for_request(view_name, view_kwargs, self._RESOURCES)
        return response


class _WebsiteViewSetWithCustomGetQueryset(WebsiteViewSet):
    def get_queryset(self):
        return Website.objects.none()


def _mount_urls_on_namespace(urls, namespace):
    urls = list(urls)
    urlpatterns = (
        url(r'^{}/'.format(namespace), include(urls, namespace=namespace)),
    )
    return urlpatterns


def _make_request_to_namespaced_url(namespace, url_name, url_kwargs, urlconf):
    request_factory = APIRequestFactory(SERVER_NAME='example.org')
    request = request_factory.get('/')
    request.versioning_scheme = NamespaceVersioning()
    request.version = namespace
    url_path = reverse(
        url_name,
        kwargs=url_kwargs,
        urlconf=urlconf,
        request=request,
    )

    client = TestClient(urlconf)
    response = client.get(url_path)
    return response
