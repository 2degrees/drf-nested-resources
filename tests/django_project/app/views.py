from django.utils.decorators import classonlymethod
from django.http.response import HttpResponse
from rest_framework.viewsets import ModelViewSet

from tests.django_project.app.models import Developer


def view(request, arg1, arg2):
    response = HttpResponse(arg1 + arg2, content_type='text/plain')
    return response


class DeveloperViewSet(ModelViewSet):

    queryset = Developer.objects.all()

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        view = super(DeveloperViewSet, cls).as_view(actions=actions, **initkwargs)
        view.is_fixture = True
        return view
