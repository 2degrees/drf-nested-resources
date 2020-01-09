from drf_nested_resources.routers import NestedResource
from drf_nested_resources.routers import Resource
from drf_nested_resources.routers import make_urlpatterns_from_resources
from . import views

_RESOURCES = [
    Resource(
        'developer',
        'developers',
        views.DeveloperViewSet,
        [
            NestedResource(
                'language',
                'languages',
                views.ProgrammingLanguageViewSet,
                parent_field_lookup='author',
            ),
        ],
    ),
]

urlpatterns = make_urlpatterns_from_resources(_RESOURCES)
