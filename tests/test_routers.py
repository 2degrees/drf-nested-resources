from django.core.urlresolvers import resolve
from nose.tools import eq_
from nose.tools import ok_
from rest_framework.reverse import reverse
from rest_framework.routers import SimpleRouter

from drf_nested_resources.routers import Route
from drf_nested_resources.routers import make_urlpatterns_from_routes
from tests.django_project.app.views import DeveloperViewSet


class TestURLPatternGeneration(object):

    def test_default_router(self):
        routes = []
        urlpatterns = make_urlpatterns_from_routes(routes)
        eq_(2, len(urlpatterns))

        url_path1 = reverse('api-root', urlconf=urlpatterns)
        eq_('/', url_path1)

        url_path2 = \
            reverse('api-root', kwargs={'format': 'json'}, urlconf=urlpatterns)
        eq_('/.json', url_path2)

    def test_routes_resolution_with_default_router(self):
        routes = [Route('developers', DeveloperViewSet)]
        urlpatterns = make_urlpatterns_from_routes(routes)

        url_path = reverse('developers-list', urlconf=urlpatterns)
        eq_('/developers/', url_path)

        view_callable, view_args, view_kwargs = resolve(url_path, urlpatterns)
        ok_(getattr(view_callable, 'is_fixture', False))
        eq_((), view_args)
        eq_({}, view_kwargs)

    def test_routes_resolution_with_custom_router(self):
        routes = [Route('developers', DeveloperViewSet)]
        urlpatterns = make_urlpatterns_from_routes(routes, SimpleRouter)
        eq_(2, len(urlpatterns))

        url_path1 = reverse('developers-list', urlconf=urlpatterns)
        eq_('/developers/', url_path1)

        url_path2 = \
            reverse('developers-detail', kwargs={'pk': 1}, urlconf=urlpatterns)
        eq_('/developers/1/', url_path2)


class TestDispatch(object):

    def test_parent_list(self):
        assert 0

    def test_parent_detail(self):
        assert 0

    def test_non_existing_parent_detail(self):
        assert 0

    def test_children_list(self):
        assert 0

    def test_child_detail(self):
        assert 0

    def test_non_existing_child_detail(self):
        assert 0


class TestSerialization(object):
    def test_parent_list(self):
        assert 0

    def test_parent_detail(self):
        assert 0

    def test_child_list(self):
        assert 0

    def test_child_detail(self):
        assert 0
