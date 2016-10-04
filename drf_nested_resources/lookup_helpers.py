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


from abc import ABCMeta, abstractmethod

from django.core.exceptions import ImproperlyConfigured
from django.db.models import ManyToManyField
from django.db.models import ManyToManyRel
from django.db.models.constants import LOOKUP_SEP


class BaseParentLookupHelper(metaclass=ABCMeta):

    def __init__(self, parent_lookup):
        super(BaseParentLookupHelper, self).__init__()
        self._parent_lookup = parent_lookup

    def __str__(self):
        return self._parent_lookup

    @abstractmethod
    def __call__(self, current_object, request):
        pass  # pragma: no cover


class SimpleParentLookupHelper(BaseParentLookupHelper):

    def __call__(self, current_object, request):
        resolved_object = current_object
        for lookup in self._parent_lookup.split(LOOKUP_SEP):
            resolved_object = getattr(resolved_object, lookup)

        return resolved_object


class RequestParentLookupHelper(BaseParentLookupHelper):

    def __init__(self, parent_lookup, request_key):
        super(RequestParentLookupHelper, self).__init__(parent_lookup)
        self._request_key = request_key

    def __call__(self, current_object, request):
        parent_object_pk = self._extract_parent_object_pk_from_request(request)
        parent_model = self._get_parent_model(current_object)
        parent_model_instance = parent_model.objects.get(pk=parent_object_pk)
        return parent_model_instance

    def _extract_parent_object_pk_from_request(self, request):
        request_kwargs = request.parser_context['kwargs']
        try:
            parent_object_pk = request_kwargs[self._request_key]
        except KeyError as exc:
            message = str(
                'Cannot find URL kwarg "{}" in current request. This '
                'type of cross-linking is not supported',
            ).format(self._request_key)
            raise ImproperlyConfigured(message) from exc
        return parent_object_pk

    def _get_parent_model(self, current_object):
        related_field = current_object._meta.get_field(self._parent_lookup)
        if isinstance(related_field, ManyToManyRel):
            relationship = related_field
        elif isinstance(related_field, ManyToManyField):
            relationship = related_field.rel
        else:
            assert False, 'field of type {!r} is not supported'.format(
                type(related_field))
        return relationship.model
