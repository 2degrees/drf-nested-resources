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

from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import HyperlinkedModelSerializer

from drf_nested_resources import DETAIL_VIEW_NAME_SUFFIX
from drf_nested_resources import LIST_VIEW_NAME_SUFFIX


class HyperlinkedNestedRelatedField(HyperlinkedRelatedField):

    def __init__(self, view_name=None, url_generator=None, **kwargs):
        super(HyperlinkedNestedRelatedField, self).__init__(
            view_name=view_name,
            **kwargs
            )
        self._url_generator = url_generator

    def use_pk_only_optimization(self):
        # Ensure that we never get PKOnlyObject in get_url since we require the
        # full instance
        return False

    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk'):
            leaf_resource_object = obj
            if obj.pk is None:
                return None

        elif hasattr(obj, 'instance'):
            leaf_resource_object = obj.instance
        else:
            assert False, 'unsupported type for obj {!r}'.format(type(obj))

        url = self._url_generator(
            view_name,
            leaf_resource_object,
            request,
            format,
        )
        return url


class HyperlinkedNestedIdentityField(HyperlinkedIdentityField):

    def __init__(self, view_name=None, url_generator=None, **kwargs):
        super(HyperlinkedNestedIdentityField, self).__init__(
            view_name=view_name,
            **kwargs
            )
        self._url_generator = url_generator

    def get_url(self, obj, view_name, request, format):
        if obj.pk is None:
            return None

        return self._url_generator(view_name, obj, request, format)


class HyperlinkedNestedModelSerializer(HyperlinkedModelSerializer):

    serializer_related_field = HyperlinkedNestedRelatedField

    serializer_url_field = HyperlinkedNestedIdentityField

    def build_url_field(self, field_name, model_class):
        field_class, field_kwargs = \
            super(HyperlinkedNestedModelSerializer, self).build_url_field(
                field_name,
                model_class,
                )
        field_kwargs['view_name'] = \
            self.Meta.resource_name + DETAIL_VIEW_NAME_SUFFIX
        field_kwargs['url_generator'] = self.Meta.url_generator

        return field_class, field_kwargs

    def build_relational_field(self, field_name, relation_info):
        super_ = super(HyperlinkedNestedModelSerializer, self)
        field_class, field_kwargs = \
            super_.build_relational_field(field_name, relation_info)

        view_name = self.Meta.view_names_by_relationship[field_name]

        if relation_info.to_many:
            view_name_suffix = LIST_VIEW_NAME_SUFFIX
            del field_kwargs['many']
        else:
            view_name_suffix = DETAIL_VIEW_NAME_SUFFIX
            field_kwargs['lookup_url_kwarg'] = view_name

        field_kwargs['view_name'] = view_name + view_name_suffix
        field_kwargs['url_generator'] = self.Meta.url_generator
        return field_class, field_kwargs
