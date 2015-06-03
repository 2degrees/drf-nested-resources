from collections import OrderedDict

from pyrecord import Record
from rest_framework.routers import DefaultRouter


Resource = Record.create_type(
    'Resource',
    'name',
    'collection_name',
    'viewset',
    'sub_resources',
    sub_resources=(),
    )


NestedResource = Resource.extend_type(
    'NestedResourceRoute',
    'parent_field_lookup',
    )


_FlattenedResource = Record.create_type(
    'FlattenedRoute',
    'name',
    'collection_name',
    'viewset',
    'ancestor_lookups_by_resource_collection_name',
    )


def make_urlpatterns_from_resources(resources, router=None):
    router = router or DefaultRouter()

    flattened_resources = _flatten_nested_resources(resources)
    for flattened_resource in flattened_resources:
        url_path = _create_url_path_from_flattened_resource(flattened_resource)
        nested_viewset = _create_nested_viewset(flattened_resource.viewset)

        router.register(url_path, nested_viewset, flattened_resource.name)
    urlpatterns = router.urls
    return tuple(urlpatterns)


def _flatten_nested_resources(
    resources,
    ancestor_lookups_by_resource_collection_name=None,
    parent_collection_name=None,
    ):
    if ancestor_lookups_by_resource_collection_name:
        ancestor_lookups_by_resource_collection_name = \
            ancestor_lookups_by_resource_collection_name.copy()
    else:
        ancestor_lookups_by_resource_collection_name = OrderedDict()

    flattened_resources = []
    for resource in resources:
        parent_lookups_by_resource_collection_name = \
            _create_ancestor_lookups_by_resource_collection_name(
                ancestor_lookups_by_resource_collection_name,
                resource,
                parent_collection_name,
                )
        flattened_resource = _FlattenedResource(
            resource.name,
            resource.collection_name,
            resource.viewset,
            parent_lookups_by_resource_collection_name,
            )
        descendant_resources = _flatten_nested_resources(
            resource.sub_resources,
            parent_lookups_by_resource_collection_name,
            resource.collection_name,
            )
        flattened_resources.extend([flattened_resource] + descendant_resources)
    return flattened_resources


def _create_ancestor_lookups_by_resource_collection_name(
    ancestor_lookups_by_resource_collection_name,
    resource,
    parent_name,
    ):
    if hasattr(resource, 'parent_field_lookup'):
        ancestor_lookups = OrderedDict(
            ancestor_lookups_by_resource_collection_name,
            **{parent_name: resource.parent_field_lookup}
            )
    else:
        ancestor_lookups = \
            ancestor_lookups_by_resource_collection_name
    return ancestor_lookups


def _create_url_path_from_flattened_resource(flattened_resource):
    url_parts = ''
    ancestors_lookups = list(
        flattened_resource.ancestor_lookups_by_resource_collection_name
            .values()
        )
    collection_names = \
        flattened_resource.ancestor_lookups_by_resource_collection_name.keys()
    for index, collection_name in enumerate(collection_names):
        next_ancestors_lookups = ancestors_lookups[index:]
        url_group_name = \
            _create_url_group_name_from_next_lookups(next_ancestors_lookups)
        url_parts += \
            r'{}/(?P<{}>[^/]+)/'.format(collection_name, url_group_name)
    url_pattern = r'{}{}'.format(url_parts, flattened_resource.collection_name)
    return url_pattern


def _create_url_group_name_from_next_lookups(next_lookups):
    # The url group names are made using the Django lookups from the perspective
    # of the child resource collection, so the lookups need to be reversed in
    # order to generate them in the correct order
    reversed_lookups = reversed(next_lookups)
    url_group_name = '__'.join([lookup for lookup in reversed_lookups])
    return url_group_name


def _create_nested_viewset(route_viewset):
    class NestedViewSet(route_viewset):
        def get_queryset(self):
            old_queryset = self.queryset

            filters = {k: v for k, v in self.kwargs.items()}
            self.queryset = self.queryset.filter(**filters)
            get_queryset = super(route_viewset, self).get_queryset()

            self.queryset = old_queryset
            return get_queryset
    return NestedViewSet

