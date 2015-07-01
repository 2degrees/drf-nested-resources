from django.test.client import Client
from django.test.client import ClientHandler


class RequestForger(Client):

    def __init__(self, urlconf, host, user=None, **kwargs):
        kwargs['SERVER_NAME'] = host
        super(RequestForger, self).__init__(**kwargs)

        self.handler = _ForgedRequestHandler(urlconf, user)


class _ForgedRequestHandler(ClientHandler):

    def __init__(self, urlconf, user, *args, **kwargs):
        super(_ForgedRequestHandler, self).__init__(*args, **kwargs)
        self._urlconf = urlconf
        self.user = user

    def get_response(self, request):
        request.urlconf = self._urlconf
        request._cached_user = self.user
        return super(_ForgedRequestHandler, self).get_response(request)
