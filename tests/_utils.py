from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.client import ClientHandler

from drf_nested_resources.routers import make_urlpatterns_from_resources


class TestClient(Client):

    def __init__(self, urlconf, environ_items=None, *args, **kwargs):
        kwargs['SERVER_NAME'] = 'example.org'
        super(TestClient, self).__init__(*args, **kwargs)

        self.handler = _TestClientHandler(urlconf, environ_items)


class _TestClientHandler(ClientHandler):

    def __init__(self, urlconf, environ_items, *args, **kwargs):
        super(_TestClientHandler, self).__init__(*args, **kwargs)
        self._urlconf = urlconf
        self._environ_items = environ_items or {}

    def get_response(self, request):
        if self._urlconf:
            request.urlconf = self._urlconf
        for header_name, header_value in self._environ_items.items():
            request.META[header_name] = header_value
        return super(_TestClientHandler, self).get_response(request)


def make_response_for_request(
    view_name,
    view_kwargs,
    resources=None,
    method_name='GET',
    environ_items=None,
    **kwargs
):
    if resources:
        urlpatterns = make_urlpatterns_from_resources(resources)
    else:
        urlpatterns = None
    client = TestClient(urlpatterns, environ_items)
    url_path = reverse(view_name, kwargs=view_kwargs, urlconf=urlpatterns)
    method = getattr(client, method_name.lower())
    response = method(url_path, **kwargs)
    return response
