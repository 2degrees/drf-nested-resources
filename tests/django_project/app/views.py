from django.http.response import HttpResponse
from django.utils.decorators import classonlymethod
from rest_framework.viewsets import ModelViewSet

from drf_nested_resources.fields import HyperlinkedNestedModelSerializer
from tests.django_project.app.models import Developer
from tests.django_project.app.models import ProgrammingLanguage
from tests.django_project.app.models import ProgrammingLanguageVersion
from tests.django_project.app.models import Website
from tests.django_project.app.models import WebsiteHost
from tests.django_project.app.models import WebsiteVisit


def view(request, arg1, arg2):
    response = HttpResponse(arg1 + arg2, content_type='text/plain')
    return response


class _DeveloperSerializer(HyperlinkedNestedModelSerializer):

    class Meta(object):

        model = Developer

        fields = ('url', 'name', 'programming_languages')


class DeveloperViewSet(ModelViewSet):

    queryset = Developer.objects.all()

    serializer_class = _DeveloperSerializer

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        view = \
            super(DeveloperViewSet, cls).as_view(actions=actions, **initkwargs)
        view.is_fixture = True
        return view


class _DeveloperSerializer2(HyperlinkedNestedModelSerializer):

    class Meta(object):

        model = Developer

        fields = ('url', 'name')


class DeveloperViewSet2(DeveloperViewSet):


    serializer_class = _DeveloperSerializer2


class _ProgrammingLanguageSerializer(HyperlinkedNestedModelSerializer):

    class Meta(object):

        model = ProgrammingLanguage

        fields = ('url', 'name', 'author', 'versions')


class ProgrammingLanguageViewSet(ModelViewSet):

    queryset = ProgrammingLanguage.objects.all()

    serializer_class = _ProgrammingLanguageSerializer


class _ProgrammingLanguageVersionSerializer(HyperlinkedNestedModelSerializer):

    class Meta(object):

        model = ProgrammingLanguageVersion

        fields = ('url', 'name')


class ProgrammingLanguageVersionViewSet(ModelViewSet):

    queryset = ProgrammingLanguageVersion.objects.all()

    serializer_class = _ProgrammingLanguageVersionSerializer


class _WebsiteSerializaer(HyperlinkedNestedModelSerializer):

    class Meta(object):

        model = Website

        fields = ('url', 'base_url', 'hosts')


class WebsiteViewSet(ModelViewSet):

    queryset = Website.objects.all()

    serializer_class = _WebsiteSerializaer


class _WebsiteVisitSerializaer(HyperlinkedNestedModelSerializer):

    class Meta(object):

        model = WebsiteVisit

        fields = ('url', 'timestamp')


class WebsiteVisitViewSet(ModelViewSet):

    queryset = WebsiteVisit.objects.all()

    serializer_class = _WebsiteVisitSerializaer


class _WebsiteHostSerializaer(HyperlinkedNestedModelSerializer):

    class Meta(object):

        model = WebsiteHost

        fields = ('name', 'url')


class WebsiteHostViewSet(ModelViewSet):

    queryset = WebsiteHost.objects.all()

    serializer_class = _WebsiteHostSerializaer
