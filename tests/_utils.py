from django.test.client import Client
from django.test.client import ClientHandler


class TestClient(Client):

    def __init__(self, urlconf, user=None, *args, **kwargs):
        super(TestClient, self).__init__(*args, **kwargs)

        self.handler = _TestClientHandler(urlconf, user)


class _TestClientHandler(ClientHandler):

    def __init__(self, urlconf, user, *args, **kwargs):
        super(_TestClientHandler, self).__init__(*args, **kwargs)
        self._urlconf = urlconf
        self.user = user

    def get_response(self, request):
        request.urlconf = self._urlconf
        request._cached_user = self.user
        return super(_TestClientHandler, self).get_response(request)
