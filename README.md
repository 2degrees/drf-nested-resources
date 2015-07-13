# drf-nested-resources

This is a django rest framework extension to allow developers to create nested
resources.

## How to use

### Configuration of nested resources

For this example we are going to create a simple API with the following
endpoints:

    /developers/
    /developers/<id>
    /developers/<id>/languages/
    /developers/<id>/languages/<id>

First we start with the following Django models:

```python
from django.db.models.base import Model
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey


class Developer(Model):

    name = CharField(max_length=20)


class ProgrammingLanguage(Model):

    name = CharField(max_length=20)

    author = ForeignKey(Developer, related_name='programming_languages')
```

We will have the two viewsets for both the `developers` and `languages` resource
collections.

```python
from rest_framework.viewsets import ModelViewSet
from drf_nested_resources.fields import HyperlinkedNestedModelSerializer


class _DeveloperSerializer(HyperlinkedNestedModelSerializer):

    class Meta(object):

        model = Developer

        fields = ('url', 'name', 'programming_languages')


class DeveloperViewSet(ModelViewSet):

    queryset = Developer.objects.all()

    serializer_class = _DeveloperSerializer


class _ProgrammingLanguageSerializer(HyperlinkedNestedModelSerializer):

    class Meta(object):

        model = ProgrammingLanguage

        fields = ('url', 'name', 'author')


class ProgrammingLanguageViewSet(ModelViewSet):

    queryset = ProgrammingLanguage.objects.all()

    serializer_class = _ProgrammingLanguageSerializer
```

The related fields in the ViewSets `author` and `programming_languages` should
follow the model representation so that `author` will give us a url for the
developer who wrote the ProgrammingLanguage and the `programming_languages`
should give us a list of urls for the ProgrammingLanguages that the Developer
wrote.

This is how you would generate the urlpatterns for them:

```python
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
                )
            ],
        ),
    ]
urlpatterns = make_urlpatterns_from_resources(_RESOURCES)
```

For more examples of different relationships and authorization check the test
suite.
