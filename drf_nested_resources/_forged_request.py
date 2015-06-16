from django.test.client import Client
from django.test.client import ClientHandler


class RequestForger(Client):

    def __init__(self, urlconf, *args, **kwargs):
        super(RequestForger, self).__init__(*args, **kwargs)

        self.handler = _ForgedRequestHandler(urlconf)


class _ForgedRequestHandler(ClientHandler):

    def __init__(self, urlconf, *args, **kwargs):
        super(_ForgedRequestHandler, self).__init__(*args, **kwargs)
        self._urlconf = urlconf

    def get_response(self, request):
        request.urlconf = self._urlconf
        return super(_ForgedRequestHandler, self).get_response(request)
