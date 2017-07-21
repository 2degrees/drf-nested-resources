from drf_nested_resources.routers import Resource, NestedResource, \
    make_urlpatterns_from_resources
from tests.django_project.app.views import DeveloperViewSet, \
    ProgrammingLanguageViewSet


_RESOURCES = [
    Resource(
        'developer',
        'developers',
        DeveloperViewSet,
        [
            NestedResource(
                'language',
                'languages',
                ProgrammingLanguageViewSet,
                parent_field_lookup='author',
            ),
        ],
    ),
]

urlpatterns = make_urlpatterns_from_resources(_RESOURCES)
