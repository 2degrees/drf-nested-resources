from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import HyperlinkedModelSerializer

from drf_nested_resources import DETAIL_VIEW_NAME_SUFFIX
from drf_nested_resources import LIST_VIEW_NAME_SUFFIX


class HyperlinkedNestedRelatedField(HyperlinkedRelatedField):

    def __init__(self, view_name=None, urlvars_by_view_name=None, **kwargs):
        super(HyperlinkedNestedRelatedField, self).__init__(
            view_name=view_name,
            **kwargs
            )
        assert urlvars_by_view_name, 'urlvars_by_view_name cannot be empty!'
        self.urlvars_by_view_name = urlvars_by_view_name

    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk'):
            pk = obj.pk
        elif hasattr(obj, 'instance'):
            pk = obj.instance.pk
        else:
            assert False, 'unsupported type for obj {!r}'.format(type(obj))

        if pk is None:
            return None

        current_view_kwargs = request.parser_context['kwargs']

        view_urlvars = self.urlvars_by_view_name[view_name]
        kwargs = {}
        for resource_name in view_urlvars:
            kwargs[resource_name] = current_view_kwargs.get(resource_name, pk)

        url = self.reverse(
            view_name,
            kwargs=kwargs,
            request=request,
            format=format,
            )
        return url


class HyperlinkedNestedIdentityField(HyperlinkedIdentityField):

    def __init__(self, view_name=None, urlvars_by_view_name=None, **kwargs):
        super(HyperlinkedNestedIdentityField, self).__init__(
            view_name=view_name,
            **kwargs
            )
        assert urlvars_by_view_name, 'urlvars_by_view_name cannot be empty!'
        self.urlvars_by_view_name = urlvars_by_view_name

    def get_url(self, obj, view_name, request, format):
        if obj.pk is None:
            return None

        current_view_kwargs = request.parser_context['kwargs']
        view_urlvars = self.urlvars_by_view_name[view_name]
        kwargs = {}
        for resource_name in view_urlvars:
            kwargs[resource_name] = \
                current_view_kwargs.get(resource_name, obj.pk)

        url = self.reverse(
            view_name,
            kwargs=kwargs,
            request=request,
            format=format,
            )
        return url


class HyperlinkedNestedModelSerializer(HyperlinkedModelSerializer):

    serializer_related_field = HyperlinkedNestedRelatedField

    serializer_url_field = HyperlinkedNestedIdentityField

    def build_url_field(self, field_name, model_class):
        field_class, field_kwargs = \
            super(HyperlinkedNestedModelSerializer, self).build_url_field(
                field_name,
                model_class,
                )
        field_kwargs['view_name'] = \
            self.Meta.resource_name + DETAIL_VIEW_NAME_SUFFIX
        field_kwargs['urlvars_by_view_name'] = self.Meta.urlvars_by_view_name

        return field_class, field_kwargs

    def build_relational_field(self, field_name, relation_info):
        super_ = super(HyperlinkedNestedModelSerializer, self)
        field_class, field_kwargs = \
            super_.build_relational_field(field_name, relation_info)

        if relation_info.to_many:
            view_name_suffix = LIST_VIEW_NAME_SUFFIX
            del field_kwargs['many']
        else:
            view_name_suffix = DETAIL_VIEW_NAME_SUFFIX

        view_name = self.Meta.view_names_by_relationship[field_name]
        field_kwargs['view_name'] = view_name + view_name_suffix
        field_kwargs['urlvars_by_view_name'] = self.Meta.urlvars_by_view_name
        return field_class, field_kwargs
