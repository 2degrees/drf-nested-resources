from unittest.mock import patch

from django.test.utils import override_settings
from nose.tools import assert_not_in
from nose.tools.trivial import eq_
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated

from drf_nested_resources.routers import NestedResource
from drf_nested_resources.routers import Resource
from tests._testcases import FixtureTestCase
from tests._utils import make_response_for_request
from tests.django_project.app.views import DeveloperViewSet
from tests.django_project.app.views import ProgrammingLanguageVersionViewSet
from tests.django_project.app.views import ProgrammingLanguageViewSet


class TestPermissions(FixtureTestCase):
    def test_access_to_authorized_child_of_authorized_parent(self):
        self._assert_permission_granted_to_child_resource(
            _HeadersRequiredDeveloperViewSet,
            ProgrammingLanguageViewSet,
            environ_items=_HasRequiredEnvironPermission.VARIABLES,
        )

    def test_access_to_authorized_child_list_of_authorized_parent(self):
        self._assert_permission_granted_to_child_resource_list(
            _HeadersRequiredDeveloperViewSet,
            ProgrammingLanguageViewSet,
            environ_items=_HasRequiredEnvironPermission.VARIABLES,
        )

    def test_access_to_unauthorized_child_of_authorized_parent(self):
        self._assert_permission_denied_to_child_resource(
            DeveloperViewSet,
            AccessDeniedProgrammingLanguageViewSet,
        )

    def test_access_to_unauthorized_child_list_of_authorized_parent(self):
        self._assert_permission_denied_to_child_resource_list(
            DeveloperViewSet,
            AccessDeniedProgrammingLanguageViewSet,
        )

    def test_access_to_authorized_child_of_unauthorized_parent(self):
        self._assert_permission_denied_to_child_resource(
            _HeadersRequiredDeveloperViewSet,
            ProgrammingLanguageViewSet,
        )

    def test_access_to_authorized_child_list_of_unauthorized_parent(self):
        self._assert_permission_denied_to_child_resource_list(
            _HeadersRequiredDeveloperViewSet,
            ProgrammingLanguageViewSet,
        )

    def test_access_to_unauthorized_child_of_unauthorized_parent(self):
        self._assert_permission_denied_to_child_resource(
            AccessDeniedDeveloperViewSet,
            AccessDeniedProgrammingLanguageViewSet,
        )

    def test_access_to_unauthorized_child_list_of_unauthorized_parent(self):
        self._assert_permission_denied_to_child_resource_list(
            AccessDeniedDeveloperViewSet,
            AccessDeniedProgrammingLanguageViewSet,
        )

    def test_access_to_unauthorized_child_detail_route_of_unauthorized_parent(
        self,
    ):
        self._assert_permission_denied_to_child_resource(
            AccessDeniedDeveloperViewSet,
            ProgrammingLanguageViewSet,
            url_name='language-type',
        )

    def test_access_to_authorized_child_detail_route_of_authorized_parent(self):
        self._assert_permission_granted_to_child_resource(
            DeveloperViewSet,
            ProgrammingLanguageViewSet,
            url_name='language-type',
        )

    def test_access_to_authorized_child_detail_route_of_unauthorized_child(
        self,
    ):
        self._assert_permission_denied_to_child_resource(
            AccessDeniedDeveloperViewSet,
            ProgrammingLanguageViewSet,
            url_name='language-type',
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

    def test_access_to_authorized_grandchild_list_of_unauthorized_grandparent(
        self):
        url_name = 'version-list'
        urlvars = {
            'developer': self.developer1.pk,
            'language': self.programming_language1.pk,
        }
        self._assert_permission_denied_to_child_resource(
            AccessDeniedDeveloperViewSet,
            ProgrammingLanguageViewSet,
            url_name=url_name,
            urlvars=urlvars,
        )

    def test_request_copied_correctly(self):
        resources = \
            self._build_resources(DeveloperViewSet, ProgrammingLanguageViewSet)

        http_host = 'www.example.org'

        patched_method = \
            _patch_method(DeveloperViewSet, 'check_object_permissions')
        with patched_method as check_obj_permissions_mock:
            make_response_for_request(
                'language-list',
                {'developer': self.developer1.pk},
                resources,
                method_name='POST',
                environ_items={
                    'QUERY_STRING': 'foo=bar',
                    'HTTP_HOST': http_host,
                },
                data={'key': 'value'},
            )

        eq_(1, check_obj_permissions_mock.call_count)

        call_args = check_obj_permissions_mock.call_args
        request = call_args[0][0]

        # Ensure conversion to HEAD request
        eq_('HEAD', request.method)
        eq_('', request.META['QUERY_STRING'])
        eq_(0, len(request.META['wsgi.input']))
        eq_('0', request.META['CONTENT_LENGTH'])
        assert_not_in('CONTENT_TYPE', request.META)

        # Ensure other WSGI environment variables remain unchanged
        eq_(http_host, request.META.get('HTTP_HOST'))

    @override_settings(ROOT_URLCONF='tests.django_project.testing_urls')
    def test_no_explicit_urlconf(self):
        response = make_response_for_request(
            'language-list',
            {'developer': self.developer1.pk},
            None,
        )
        eq_(200, response.status_code)

    def _assert_permission_granted_to_child_resource(
        self,
        parent_view_set,
        child_view_set,
        url_name=None,
        environ_items=None,
    ):
        response = self._get_response_from_child_resource(
            parent_view_set,
            child_view_set,
            environ_items=environ_items,
            url_name=url_name,
        )
        eq_(200, response.status_code)

    def _assert_permission_granted_to_child_resource_list(
        self,
        parent_view_set,
        child_view_set,
        environ_items=None,
    ):
        response = self._get_response_from_child_resource_list(
            parent_view_set,
            child_view_set,
            environ_items=environ_items,
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

    def _assert_permission_denied_to_child_resource_list(
        self,
        parent_view_set,
        child_view_set,
        url_name=None,
        urlvars=None,
    ):
        response = self._get_response_from_child_resource_list(
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
        environ_items=None,
    ):
        urlvars = urlvars or {
            'developer': self.developer1.pk,
            'language': self.programming_language1.pk,
        }
        response = make_response_for_request(
            url_name or 'language-detail',
            urlvars,
            self._build_resources(parent_view_set, child_view_set),
            environ_items=environ_items,
        )
        return response

    def _get_response_from_child_resource_list(
        self,
        parent_view_set,
        child_view_set,
        url_name=None,
        urlvars=None,
        environ_items=None,
    ):
        response = make_response_for_request(
            url_name or 'language-list',
            urlvars or {'developer': self.developer1.pk},
            self._build_resources(parent_view_set, child_view_set),
            environ_items=environ_items,
        )
        return response

    @staticmethod
    def _build_resources(parent_view_set, child_view_set):
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


class _HasRequiredEnvironPermission(BasePermission):
    VARIABLES = {'X_FOO': 'Bar'}

    def has_permission(self, request, view):
        return self._check_required_environ_variables(request)

    def has_object_permission(self, request, view, obj):
        return self._check_required_environ_variables(request)

    @classmethod
    def _check_required_environ_variables(cls, request):
        relevant_environ_items = {}
        for variable_name in cls.VARIABLES:
            variable_value = request.META.get(variable_name)
            relevant_environ_items[variable_name] = variable_value
        return relevant_environ_items == cls.VARIABLES


class AccessDeniedDeveloperViewSet(DeveloperViewSet):
    permission_classes = (_DenyAll,)


class AccessDeniedProgrammingLanguageViewSet(ProgrammingLanguageViewSet):
    permission_classes = (_DenyAll,)


class IsAuthenticatedDeveloperViewSet(DeveloperViewSet):
    permission_classes = (IsAuthenticated,)


class _HeadersRequiredDeveloperViewSet(DeveloperViewSet):
    permission_classes = (_HasRequiredEnvironPermission,)


def _patch_method(cls, method_name):
    python_path_to_method = _get_python_path_to_class_method(cls, method_name)
    return patch(python_path_to_method)


def _get_python_path_to_class_method(cls, method_name):
    import_path = '{}.{}.{}'.format(cls.__module__, cls.__name__, method_name)
    return import_path
