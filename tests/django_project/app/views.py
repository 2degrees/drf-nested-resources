from django.http.response import HttpResponse
from django.utils.decorators import classonlymethod
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from tests.django_project.app.models import Developer
from tests.django_project.app.models import ProgrammingLanguage
from tests.django_project.app.models import ProgrammingLanguageVersion


def view(request, arg1, arg2):
    response = HttpResponse(arg1 + arg2, content_type='text/plain')
    return response


class _DeveloperSerializer(ModelSerializer):

    class Meta(object):

        model = Developer

        fields = ('name', )


class DeveloperViewSet(ModelViewSet):

    queryset = Developer.objects.all()

    serializer_class = _DeveloperSerializer

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        view = \
            super(DeveloperViewSet, cls).as_view(actions=actions, **initkwargs)
        view.is_fixture = True
        return view


class _ProgrammingLanguageSerializer(ModelSerializer):

    class Meta(object):

        model = ProgrammingLanguage

        fields = ('name', )


class ProgrammingLanguageViewSet(ModelViewSet):

    queryset = ProgrammingLanguage.objects.all()

    serializer_class = _ProgrammingLanguageSerializer


class _ProgrammingLanguageVersionSerializer(ModelSerializer):

    class Meta(object):

        model = ProgrammingLanguageVersion

        fields = ('name', )


class ProgrammingLanguageVersionViewSet(ModelViewSet):

    queryset = ProgrammingLanguageVersion.objects.all()

    serializer_class = _ProgrammingLanguageVersionSerializer
