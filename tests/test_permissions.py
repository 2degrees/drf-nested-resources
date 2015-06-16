from django.core.urlresolvers import reverse
from nose.tools.trivial import eq_
from rest_framework.permissions import BasePermission

from drf_nested_resources.routers import NestedResource
from drf_nested_resources.routers import Resource
from drf_nested_resources.routers import make_urlpatterns_from_resources
from tests._testcases import FixtureTestCase
from tests._utils import TestClient
from tests.django_project.app.views import DeveloperViewSet
from tests.django_project.app.views import ProgrammingLanguageVersionViewSet
from tests.django_project.app.views import ProgrammingLanguageViewSet


class TestPermissions(FixtureTestCase):

    def test_access_to_authorized_child_of_authorized_parent(self):
        self._assert_permission_granted_to_child_resource(
            DeveloperViewSet,
            ProgrammingLanguageViewSet,
            )

    def test_access_to_unauthorized_child_of_authorized_parent(self):
        self._assert_permission_denied_to_child_resource(
            DeveloperViewSet,
            AccessDeniedProgrammingLanguageViewSet,
            )

    def test_access_to_authorized_child_of_unauthorized_parent(self):
        self._assert_permission_denied_to_child_resource(
            AccessDeniedDeveloperViewSet,
            ProgrammingLanguageViewSet,
            )

    def test_access_to_unauthorized_child_of_unauthorized_parent(self):
        self._assert_permission_denied_to_child_resource(
            AccessDeniedDeveloperViewSet,
            AccessDeniedProgrammingLanguageViewSet,
            )

    def test_access_to_authorized_grandchild_of_unauthorized_grandparent(self):
        url_name = 'version-detail'
        urlvars = {
            'developer': self.developer1.pk,
            'language': self.programming_language1.pk,
            'version': self.programming_language_version.pk,
            }
        self._assert_permission_denied_to_child_resource(
            AccessDeniedDeveloperViewSet,
            ProgrammingLanguageViewSet,
            url_name=url_name,
            urlvars=urlvars,
            )

    def _assert_permission_granted_to_child_resource(
        self,
        parent_view_set,
        child_view_set,
        ):
        response = self._get_response_from_child_resource(
            parent_view_set,
            child_view_set,
            )
        eq_(200, response.status_code)

    def _assert_permission_denied_to_child_resource(
        self,
        parent_view_set,
        child_view_set,
        url_name=None,
        urlvars=None,
        ):
        response = self._get_response_from_child_resource(
            parent_view_set,
            child_view_set,
            url_name,
            urlvars,
            )
        eq_(403, response.status_code)

    def _get_response_from_child_resource(
        self,
        parent_view_set,
        child_view_set,
        url_name=None,
        urlvars=None,
        ):
        resources = self._build_resources(parent_view_set, child_view_set)
        urlpatterns = make_urlpatterns_from_resources(resources)

        client = TestClient(urlpatterns)

        url_name = url_name or 'language-detail'
        urlvars = urlvars or {
            'developer': self.developer1.pk,
            'language': self.programming_language1.pk,
            }
        url_path = reverse(url_name, kwargs=urlvars, urlconf=urlpatterns)
        response = client.get(url_path)
        return response

    def _build_resources(self, parent_view_set, child_view_set):
        resources = [
            Resource(
                'developer',
                'developers',
                parent_view_set,
                [
                    NestedResource(
                        'language',
                        'languages',
                        child_view_set,
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
        return resources


class _DenyAll(BasePermission):

    def has_permission(self, request, view):
        return False

    def has_object_permission(self, request, view, obj):
        return False


class AccessDeniedDeveloperViewSet(DeveloperViewSet):

    permission_classes = (_DenyAll, )


class AccessDeniedProgrammingLanguageViewSet(ProgrammingLanguageViewSet):

    permission_classes = (_DenyAll, )
