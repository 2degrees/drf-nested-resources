from collections import OrderedDict
from collections import defaultdict
from re import IGNORECASE
from re import compile as compile_regex

from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.related import ManyToManyRel
from django.db.models.fields.related import OneToOneRel
from pyrecord import Record
from rest_framework.routers import DefaultRouter

from drf_nested_resources import DETAIL_VIEW_NAME_SUFFIX
from drf_nested_resources import LIST_VIEW_NAME_SUFFIX


Resource = Record.create_type(
    'Resource',
    'name',
    'collection_name',
    'viewset',
    'sub_resources',
    sub_resources=(),
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
    'ancestor_collection_name_by_resource_name'
    )


_VALID_PYTHON_IDENTIFIER_RE = compile_regex(r"^[a-z_]\w*$", IGNORECASE)


def make_urlpatterns_from_resources(resources, router_class=None):
    router_class = router_class or DefaultRouter
    nested_router_class = _create_nested_route_router(router_class, resources)
    router = nested_router_class()

    relationships_by_resource_name = defaultdict(dict)
    _populate_resource_relationships(resources, relationships_by_resource_name)

    flattened_resources = _flatten_nested_resources(resources)

    for flattened_resource in flattened_resources:
        flattened_resource.name = _format_resource_name(flattened_resource.name)

        url_path = _create_url_path_from_flattened_resource(flattened_resource)
        nested_viewset = _create_nested_viewset(
            flattened_resource,
            relationships_by_resource_name,
            )

        router.register(url_path, nested_viewset, flattened_resource.name)
    urlpatterns = router.urls
    return tuple(urlpatterns)


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

        _populate_resource_relationships(
            resource.sub_resources,
            relationships_by_resource_name,
            resource.name,
            )


def _get_reverse_relationship_name(parent_field_lookup, model):
    model_options = model._meta
    direct_parent_lookup, _, indirect_parent_lookups = \
        parent_field_lookup.partition(LOOKUP_SEP)
    field = model_options.get_field_by_name(direct_parent_lookup)[0]

    if isinstance(field, (OneToOneRel, ManyToManyRel)):
        relationship = field
    elif isinstance(field, (ForeignKey, ManyToManyField)):
        relationship = field.rel
    else:
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
            relational_routes = kwargs.pop('relational_routes')
            super(NestedViewSet, self).__init__(*args, **kwargs)
            self._relational_routes = relational_routes
            urlvars_by_view_name = {}
            for route in self.relational_routes:
                detail_route_name = route.name + DETAIL_VIEW_NAME_SUFFIX
                list_route_name = route.name + LIST_VIEW_NAME_SUFFIX
                ancestor_urlvars = tuple(
                    route.ancestor_collection_name_by_resource_name.keys(),
                    )

                urlvars_by_view_name[list_route_name] = \
                    ancestor_urlvars[:-1]
                urlvars_by_view_name[detail_route_name] = ancestor_urlvars
            self._urlvars_by_view_name = urlvars_by_view_name

        @property
        def relational_routes(self):
            return self._relational_routes

        def get_serializer_class(self):
            base_serializer_class = \
                super(NestedViewSet, self).get_serializer_class()

            class NestedSerializer(base_serializer_class):

                class Meta(base_serializer_class.Meta):
                    urlvars_by_view_name = self._urlvars_by_view_name

                    resource_name = flattened_resource.name

                    view_names_by_relationship = \
                        relationships_by_resource_name[resource_name]

            return NestedSerializer

        def get_queryset(self):
            original_queryset = self.queryset

            filters = {}
            ancestor_lookups = []
            resource_names_and_lookups = tuple(
                flattened_resource.ancestor_lookup_by_resource_name.items(),
                )
            for resource_name, lookup in reversed(resource_names_and_lookups):
                urlvar_value = self.kwargs.get(resource_name)
                if not urlvar_value:
                    continue

                ancestor_lookups.append(lookup)
                lookup = LOOKUP_SEP.join(ancestor_lookups)
                filters[lookup] = urlvar_value
            self.queryset = self.queryset.filter(**filters)
            queryset = super(route_viewset, self).get_queryset()

            self.queryset = original_queryset
            return queryset

    NestedViewSet.__name__ = '{}{}'.format(flattened_resource.name, 'ViewSet')
    return NestedViewSet
