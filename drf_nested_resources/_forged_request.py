##############################################################################
#
# Copyright (c) 2015-2017, 2degrees Limited.
# All Rights Reserved.
#
# This file is part of drf-nested-resources
# <https://github.com/2degrees/drf-nested-resources>, which is subject to the
# provisions of the BSD at
# <http://dev.2degreesnetwork.com/p/2degrees-license.html>. A copy of the
# license should accompany this distribution. THIS SOFTWARE IS PROVIDED "AS IS"
# AND ANY AND ALL EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST
# INFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

from django.test.client import Client, FakePayload
from django.test.client import ClientHandler


class RequestForger(Client):
    def __init__(self, original_request):
        environ_overrides = \
            {'wsgi.input': FakePayload(b''), 'CONTENT_LENGTH': '0'}
        new_environ = dict(original_request.environ, **environ_overrides)
        new_environ.pop('CONTENT_TYPE', None)
        super(RequestForger, self).__init__(**new_environ)

        self.handler = _ForgedRequestHandler(original_request.urlconf)


class _ForgedRequestHandler(ClientHandler):
    def __init__(self, urlconf):
        super(_ForgedRequestHandler, self).__init__()
        self._urlconf = urlconf

    def get_response(self, request):
        request.urlconf = self._urlconf
        return super(_ForgedRequestHandler, self).get_response(request)
