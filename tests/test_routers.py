from django.core.urlresolvers import resolve
from nose.tools import assert_raises
from django.conf.urls import url
from django.conf.urls import include
from nose.tools import eq_
from nose.tools import ok_
from rest_framework.reverse import reverse
from rest_framework.routers import SimpleRouter

from drf_nested_resources.routers import NestedResource
from drf_nested_resources.routers import Resource
from drf_nested_resources.routers import make_urlpatterns_from_resources
from tests._testcases import FixtureTestCase
from tests._utils import TestClient
from tests.django_project.app.models import Website
from tests.django_project.app.models import WebsiteVisit
from tests.django_project.app.views import DeveloperViewSet
from tests.django_project.app.views import DeveloperViewSet2
from tests.django_project.app.views import ProgrammingLanguageVersionViewSet
from tests.django_project.app.views import ProgrammingLanguageViewSet
from tests.django_project.app.views import WebsiteHostViewSet
from tests.django_project.app.views import WebsiteViewSet
from tests.django_project.app.views import WebsiteVisitViewSet


class TestURLPatternGeneration(object):

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
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'developer-detail',
            kwargs={'developer': self.developer1.pk},
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        response_data = response.data
        expected_languages_url = reverse(
            'language-list',
            kwargs={'developer': self.developer1.pk},
            urlconf=urlpatterns,
            )
        languages_url = response_data['programming_languages']
        ok_(languages_url.endswith(expected_languages_url))
        eq_(200, response.status_code)

    def test_parent_list(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse('developer-list', urlconf=urlpatterns)
        response = client.get(url_path)
        eq_(200, response.status_code)

    def test_parent_list_mounted_on_different_urlpath(self):
        api_urls = list(make_urlpatterns_from_resources(self._RESOURCES))
        urlpatterns = (url(r'^api/', include(api_urls)),)

        client = TestClient(urlpatterns)

        url_path = reverse('developer-list', urlconf=urlpatterns)
        response = client.get(url_path)
        eq_(200, response.status_code)

    def test_non_existing_parent_detail(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'developer-detail',
            kwargs={'developer': self.non_existing_developer_pk},
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        eq_(404, response.status_code)

    def test_child_detail(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'language-detail',
            kwargs={
                'developer': self.developer1.pk,
                'language': self.programming_language1.pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        eq_(200, response.status_code)

    def test_child_list(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'language-list',
            kwargs={'developer': self.developer1.pk},
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        eq_(200, response.status_code)

    def test_child_detail_with_wrong_parent(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'language-detail',
            kwargs={
                'developer': self.developer1.pk,
                'language': self.programming_language2.pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        eq_(404, response.status_code)

    def test_child_detail_with_non_existing_parent(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'language-detail',
            kwargs={
                'developer': self.non_existing_developer_pk,
                'language': self.programming_language1.pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        eq_(404, response.status_code)

    def test_child_list_with_non_existing_parent(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'language-list',
            kwargs={'developer': self.non_existing_developer_pk},
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
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
        urlpatterns = make_urlpatterns_from_resources(resources)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'host-detail',
            kwargs={
                'website': self.website.pk,
                'host': self.website_host.pk,
                },
            urlconf=urlpatterns,
            )

        response = client.get(url_path)
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
        urlpatterns = make_urlpatterns_from_resources(resources)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'host-list',
            kwargs={
                'website': self.website.pk,
                },
            urlconf=urlpatterns,
            )

        response = client.get(url_path)
        eq_(404, response.status_code)

    def test_non_existing_child_detail(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'language-detail',
            kwargs={
                'developer': self.developer1.pk,
                'language': self.non_existing_developer_pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        eq_(404, response.status_code)

    def test_grand_child_detail(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'version-detail',
            kwargs={
                'developer': self.developer1.pk,
                'language': self.programming_language1.pk,
                'version': self.programming_language_version.pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        eq_(200, response.status_code)

    def test_detail_with_non_existing_grandparent(self):
        urlpatterns = make_urlpatterns_from_resources(self._RESOURCES)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'version-detail',
            kwargs={
                'developer': self.non_existing_developer_pk,
                'language': self.programming_language1.pk,
                'version': self.programming_language_version.pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
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
        urlpatterns = make_urlpatterns_from_resources(resources)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'version-detail',
            kwargs={
                'developer': self.developer1.pk,
                'version': self.programming_language_version.pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        eq_(200, response.status_code)

    def test_indirect_child_detail_via_one_to_one(self):
        visit = WebsiteVisit.objects.create(website=self.website)
        resources = [
            Resource(
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
                ),
            ]
        urlpatterns = make_urlpatterns_from_resources(resources)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'visit-detail',
            kwargs={
                'language': self.programming_language1.pk,
                'visit': visit.pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
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
                        parent_field_lookup='websites',
                        ),
                    ],
                ),
            ]
        urlpatterns = make_urlpatterns_from_resources(resources)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'host-detail',
            kwargs={
                'website': self.website.pk,
                'host': self.website_host.pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
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
                        parent_field_lookup='hosts',
                        ),
                    ],
                ),
            ]
        urlpatterns = make_urlpatterns_from_resources(resources)

        client = TestClient(urlpatterns)

        url_path = reverse(
            'website-detail',
            kwargs={
                'website': self.website.pk,
                'host': self.website_host.pk,
                },
            urlconf=urlpatterns,
            )
        response = client.get(url_path)
        eq_(200, response.status_code)


class _WebsiteViewSetWithCustomGetQueryset(WebsiteViewSet):

    def get_queryset(self):
        return Website.objects.none()
