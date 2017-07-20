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

from collections import OrderedDict
from collections import defaultdict
from re import IGNORECASE
from re import compile as compile_regex

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.related import ManyToManyRel
from django.db.models.fields.related import OneToOneRel
from django.http import Http404
from pyrecord import Record
from rest_framework.exceptions import NotAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.reverse import reverse
from rest_framework.routers import DefaultRouter
from rest_framework.status import HTTP_200_OK
from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.status import HTTP_403_FORBIDDEN
from rest_framework.status import HTTP_404_NOT_FOUND

from drf_nested_resources import DETAIL_VIEW_NAME_SUFFIX
from drf_nested_resources import LIST_VIEW_NAME_SUFFIX
from drf_nested_resources._forged_request import RequestForger
from drf_nested_resources.lookup_helpers import SimpleParentLookupHelper, \
    BaseParentLookupHelper

Resource = Record.create_type(
    'Resource',
    'name',
    'collection_name',
    'viewset',
    'sub_resources',
    'cross_linked_resources',
    sub_resources=(),
    cross_linked_resources=None,
)

NestedResource = Resource.extend_type(
    'NestedResource',
    'parent_field_lookup',
)

_RelationalRoute = Record.create_type(
    'RelationalRoute',
    'name',
    'collection_name',
    'viewset',
    'ancestor_lookup_by_resource_name',
    'ancestor_collection_name_by_resource_name',
)

_VALID_PYTHON_IDENTIFIER_RE = compile_regex(r"^[a-z_]\w*$", IGNORECASE)


def make_urlpatterns_from_resources(resources, router_class=None):
    _format_resource_names(resources)

    router_class = router_class or DefaultRouter
    nested_router_class = _create_nested_route_router(router_class, resources)
    router = nested_router_class()

    relationships_by_resource_name = defaultdict(dict)
    _populate_resource_relationships(resources, relationships_by_resource_name)

    flattened_resources = _flatten_nested_resources(resources)

    for flattened_resource in flattened_resources:
        url_path = _create_url_path_from_flattened_resource(flattened_resource)
        nested_viewset = _create_nested_viewset(
            flattened_resource,
            relationships_by_resource_name,
        )

        router.register(url_path, nested_viewset, flattened_resource.name)
    urlpatterns = router.urls
    return tuple(urlpatterns)


def _format_resource_names(resources):
    for resource in resources:
        resource.name = _format_resource_name(resource.name)
        _format_resource_names(resource.sub_resources)


def _format_resource_name(name):
    formatted_name = name.replace('-', '_')
    assert bool(_VALID_PYTHON_IDENTIFIER_RE.match(formatted_name))
    return formatted_name


def _create_nested_route_router(router_class, resources):
    relational_routes = _flatten_nested_resources(resources)

    class NestedRouteRouter(router_class):
        def get_routes(self, viewset):
            routes = []
            for route in super(NestedRouteRouter, self).get_routes(viewset):
                viewset_kwargs = dict(
                    route.initkwargs,
                    relational_routes=relational_routes,
                )
                route = route._replace(initkwargs=viewset_kwargs)
                routes.append(route)
            return routes

    return NestedRouteRouter


def _flatten_nested_resources(
        resources,
        ancestor_lookup_by_resource_name=None,
        ancestor_collection_name_by_resource_name=None,
        parent_name=None,
):
    if ancestor_lookup_by_resource_name:
        ancestor_lookup_by_resource_name = \
            ancestor_lookup_by_resource_name.copy()
    else:
        ancestor_lookup_by_resource_name = OrderedDict()

    if ancestor_collection_name_by_resource_name:
        ancestor_collection_name_by_resource_name = \
            ancestor_collection_name_by_resource_name.copy()
    else:
        ancestor_collection_name_by_resource_name = OrderedDict()

    relational_routes = []
    for resource in resources:
        parent_lookups_by_resource_collection_name = \
            _create_ancestor_lookup_by_resource_name(
                ancestor_lookup_by_resource_name,
                resource,
                parent_name,
            )

        resource_ancestor_collection_name_by_resource_name = \
            ancestor_collection_name_by_resource_name.copy()
        resource_ancestor_collection_name_by_resource_name = \
            _create_ancestor_collection_name_by_resource_name(
                resource_ancestor_collection_name_by_resource_name,
                resource,
            )

        flattened_resource = _RelationalRoute(
            resource.name,
            resource.collection_name,
            resource.viewset,
            parent_lookups_by_resource_collection_name,
            resource_ancestor_collection_name_by_resource_name,
        )
        descendant_resources = _flatten_nested_resources(
            resource.sub_resources,
            parent_lookups_by_resource_collection_name,
            resource_ancestor_collection_name_by_resource_name,
            resource.name,
        )
        relational_routes.extend([flattened_resource] + descendant_resources)
    return relational_routes


def _populate_resource_relationships(
        resources,
        relationships_by_resource_name,
        parent_name=None,
):
    for resource in resources:
        parent_field_lookup = getattr(resource, 'parent_field_lookup', None)
        if parent_field_lookup:
            resource_relationships = \
                relationships_by_resource_name[resource.name]
            resource_relationships[parent_field_lookup] = parent_name

            parent_relationships = relationships_by_resource_name[parent_name]
            reverse_relationship_name = _get_reverse_relationship_name(
                parent_field_lookup,
                resource.viewset.queryset.model,
            )
            parent_relationships[reverse_relationship_name] = resource.name

        cross_linked_resources = resource.cross_linked_resources
        if cross_linked_resources:
            resource_relationships = \
                relationships_by_resource_name[resource.name]
            for field_name, linked_resource in cross_linked_resources.items():
                resource_relationships[field_name] = linked_resource.name
                reverse_relationship_name = _get_reverse_relationship_name(
                    field_name,
                    resource.viewset.queryset.model,
                )
                related_resource_relationships = \
                    relationships_by_resource_name[linked_resource.name]
                related_resource_relationships[reverse_relationship_name] = \
                    resource.name

        _populate_resource_relationships(
            resource.sub_resources,
            relationships_by_resource_name,
            resource.name,
        )


def _get_reverse_relationship_name(parent_field_lookup, model):
    model_options = model._meta
    direct_parent_lookup, _, indirect_parent_lookups = \
        str(parent_field_lookup).partition(LOOKUP_SEP)
    field = model_options.get_field(direct_parent_lookup)

    if isinstance(field, (OneToOneRel, ManyToManyRel)):
        relationship = field
    elif isinstance(field, (ForeignKey, ManyToManyField)):
        relationship = field.rel
    else:  # pragma: no cover
        assert False, 'field of type {!r} is not supported'.format(type(field))

    if indirect_parent_lookups:
        reverse_relationship_name = _get_reverse_relationship_name(
            indirect_parent_lookups,
            relationship.model,
        )
    else:
        reverse_relationship_name = relationship.name
    return reverse_relationship_name


def _create_ancestor_lookup_by_resource_name(
        ancestor_lookup_by_resource_name,
        resource,
        parent_name,
):
    if hasattr(resource, 'parent_field_lookup'):
        ancestor_lookups = OrderedDict(
            ancestor_lookup_by_resource_name,
            **{parent_name: resource.parent_field_lookup}
        )
    else:
        ancestor_lookups = \
            ancestor_lookup_by_resource_name
    return ancestor_lookups


def _create_ancestor_collection_name_by_resource_name(
        ancestor_collection_name_by_resource_name,
        resource,
):
    ancestor_collection_name_by_resource_name[resource.name] = \
        resource.collection_name
    return ancestor_collection_name_by_resource_name


def _create_url_path_from_flattened_resource(flattened_resource):
    url_parts = ''
    ancestry = flattened_resource.ancestor_collection_name_by_resource_name
    ancestor_count = len(ancestry)
    for index, (resource_name, collection_name) in enumerate(ancestry.items()):
        if index == (ancestor_count - 1):
            url_parts += collection_name
        else:
            url_parts += \
                r'{}/(?P<{}>[^/.]+)/'.format(collection_name, resource_name)
    return url_parts


def _create_nested_viewset(flattened_resource, relationships_by_resource_name):
    route_viewset = flattened_resource.viewset

    class NestedViewSet(route_viewset):

        lookup_url_kwarg = flattened_resource.name

        def __init__(self, *args, **kwargs):
            relational_routes = kwargs.pop('relational_routes', ())
            super(NestedViewSet, self).__init__(*args, **kwargs)
            self._url_generator = _URLGenerator(relational_routes)

        @property
        def relational_routes(self):
            return self._relational_routes

        def get_serializer_class(self):
            base_serializer_class = \
                super(NestedViewSet, self).get_serializer_class()

            class NestedSerializer(base_serializer_class):
                class Meta(base_serializer_class.Meta):
                    url_generator = self._url_generator

                    resource_name = flattened_resource.name

                    view_names_by_relationship = \
                        relationships_by_resource_name[resource_name]

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

                    is_creation_or_update = hasattr(self, 'initial_data')
                    field_forced_to_ancestor = \
                        getattr(self.Meta, 'field_forced_to_ancestor', None)
                    if is_creation_or_update and field_forced_to_ancestor:
                        field = self.fields[field_forced_to_ancestor]
                        ancestor_object = \
                            _extract_ancestor_object_from_field(field)
                        ancestor_url = self.Meta.url_generator(
                            field.view_name,
                            ancestor_object,
                            field.context['request'],
                        )
                        self.initial_data[field_forced_to_ancestor] = \
                            ancestor_url

            return NestedSerializer

        def get_queryset(self):
            filters = {}
            ancestor_lookups = []
            resource_names_and_lookups = \
                _get_resource_ancestors_and_lookups(flattened_resource)
            for resource_name, lookup in resource_names_and_lookups:
                urlvar_value = self.kwargs[resource_name]
                ancestor_lookups.append(lookup)
                lookup = LOOKUP_SEP.join(str(_) for _ in ancestor_lookups)
                filters[lookup] = urlvar_value
            queryset = super(NestedViewSet, self).get_queryset()
            queryset = queryset.filter(**filters)
            return queryset

        def check_object_permissions(self, request, obj):
            super(NestedViewSet, self).check_object_permissions(request, obj)
            self._check_permissions(request)

        def check_permissions(self, request):
            super(NestedViewSet, self).check_permissions(request)
            self._check_permissions(request)

        def _check_permissions(self, request):
            status = self._get_status_for_parent_resource_request(request)
            if status in (None, HTTP_200_OK):
                pass
            elif status == HTTP_404_NOT_FOUND:
                raise Http404()
            elif status == HTTP_403_FORBIDDEN:
                raise PermissionDenied()
            elif status == HTTP_401_UNAUTHORIZED:
                raise NotAuthenticated()
            else:
                assert False, 'Status code {} is not handled'.format(status)

        def _get_status_for_parent_resource_request(self, request):
            urlconf = \
                getattr(request._request, 'urlconf', settings.ROOT_URLCONF)

            parent_detail_view_url = \
                self._get_parent_resource_detail_view_url(request)

            if parent_detail_view_url:
                request_forger = RequestForger(request)
                response = request_forger.head(parent_detail_view_url)
                status_code = response.status_code
            else:
                status_code = None

            return status_code

        def _get_parent_resource_detail_view_url(self, request):
            ancestors_and_lookups = \
                _get_resource_ancestors_and_lookups(flattened_resource)
            try:
                parent_base_name = next(ancestors_and_lookups)[0]
            except StopIteration:
                return

            parent_model_class = \
                self._url_generator.get_model_class_for_resource(
                    parent_base_name,
                )
            parent_object_pk = self.kwargs[parent_base_name]

            try:
                parent_model_instance = parent_model_class.objects.get(
                    pk=parent_object_pk,
                )
            except ObjectDoesNotExist as exc:
                raise Http404() from exc

            parent_detail_view_name = parent_base_name + DETAIL_VIEW_NAME_SUFFIX
            parent_detail_view_url = self._url_generator(
                parent_detail_view_name,
                parent_model_instance,
                request,
            )
            return parent_detail_view_url

    NestedViewSet.__name__ = '{}{}'.format(flattened_resource.name, 'ViewSet')
    return NestedViewSet


def _get_resource_ancestors_and_lookups(flattened_resource):
    resource_names_and_lookups = \
        tuple(flattened_resource.ancestor_lookup_by_resource_name.items())
    return reversed(resource_names_and_lookups)


def _extract_ancestor_object_from_field(field):
    request = field.context['request']
    urlvars = request.parser_context['kwargs']
    ancestor_pk = urlvars[field.lookup_url_kwarg]
    ancestor_object = field.queryset.get(pk=ancestor_pk)
    return ancestor_object


class _URLGenerator:

    def __init__(self, relational_routes):
        super(_URLGenerator, self).__init__()

        self._relational_route_by_resource_name = \
            {r.name: r for r in relational_routes}

    def get_model_class_for_resource(self, resource_name):
        relational_route = \
            self._relational_route_by_resource_name[resource_name]
        viewset = relational_route.viewset
        model_class = viewset.queryset.model
        return model_class

    def __call__(self, view_name, leaf_resource_object, request, format_=None):
        resource_name, separator, view_type = view_name.partition('-')
        view_name_suffix = '{}{}'.format(separator, view_type)
        self._assert_valid_view_name_suffix(view_name_suffix)

        resource_name, relation_route = \
            self._resolve_resource_and_relationships(
                resource_name,
                view_name_suffix,
            )

        view_kwargs = self._build_view_kwargs(
            leaf_resource_object,
            resource_name,
            relation_route,
            request,
        )
        url = reverse(
            view_name,
            kwargs=view_kwargs,
            request=request,
            urlconf=getattr(request, 'urlconf', None),
            format=format_,
        )
        return url

    def _resolve_resource_and_relationships(
        self,
        resource_name,
        view_name_suffix,
    ):
        relation_route = self._relational_route_by_resource_name[resource_name]
        if view_name_suffix == LIST_VIEW_NAME_SUFFIX:
            # For collection views, we must start with the parent resource,
            # which will not named after `view_name`
            ancestor_resource_names = \
                list(relation_route.ancestor_lookup_by_resource_name.keys())
            resource_name = ancestor_resource_names[-1]
            relation_route = \
                self._relational_route_by_resource_name[resource_name]
        return resource_name, relation_route

    @staticmethod
    def _build_view_kwargs(
        leaf_resource_object,
        leaf_resource_name,
        relation_route,
        request,
    ):
        current_object = leaf_resource_object
        view_kwargs = {leaf_resource_name: leaf_resource_object.pk}
        resource_names_and_parent_lookups = \
            reversed(relation_route.ancestor_lookup_by_resource_name.items())
        for resource_name, parent_lookup in resource_names_and_parent_lookups:
            if isinstance(parent_lookup, str):
                parent_lookup_helper = SimpleParentLookupHelper(parent_lookup)
            elif isinstance(parent_lookup, BaseParentLookupHelper):
                parent_lookup_helper = parent_lookup
            else:
                assert False, \
                    'parent lookup must be either a string or lookup helper'
            current_object = parent_lookup_helper(current_object, request)
            view_kwargs[resource_name] = current_object.pk
        return view_kwargs

    @staticmethod
    def _assert_valid_view_name_suffix(view_name_suffix):
        valid_suffixes = (DETAIL_VIEW_NAME_SUFFIX, LIST_VIEW_NAME_SUFFIX)
        assert view_name_suffix in valid_suffixes, \
            'view name suffix must be one of {}'.format(valid_suffixes)
