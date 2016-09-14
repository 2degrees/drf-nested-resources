##############################################################################
#
# Copyright (c) 2015-2016, 2degrees Limited.
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
