from django.core.urlresolvers import reverse
from nose.tools import eq_
from rest_framework.compat import RequestFactory
from rest_framework.relations import PKOnlyObject
from rest_framework.request import Request

from drf_nested_resources.fields import HyperlinkedNestedIdentityField


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
        eq_(None, url)

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


def _make_django_request(view_name, view_kwargs):
    request_factory = RequestFactory()
    url_path = reverse(view_name, kwargs=view_kwargs)
    django_request = request_factory.get(url_path)
    django_request.resolver_match = (view_name, (), view_kwargs)
    return django_request


def _make_drf_request(django_request):
    view_kwargs = django_request.resolver_match[2]
    drf_request = \
        Request(django_request, parser_context={'kwargs': view_kwargs})
    return drf_request
