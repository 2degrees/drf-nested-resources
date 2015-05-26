from pyrecord import Record
from rest_framework.routers import DefaultRouter


Route = Record.create_type(
    'Route',
    'base_name',
    'viewset',
    'sub_routes',
    sub_routes=(),
    )


NestedRoute = Route.extend_type('NestedRoute', 'parent_field_lookup')


def make_urlpatterns_from_routes(routes, base_router_class=DefaultRouter):
    router = base_router_class()
    for route in routes:
        router.register(route.base_name, route.viewset, route.base_name)
    urlpatterns = router.urls
    return tuple(urlpatterns)
