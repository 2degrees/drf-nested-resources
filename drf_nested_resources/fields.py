from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import HyperlinkedModelSerializer


class HyperlinkedNestedRelatedField(HyperlinkedRelatedField):

    def __init__(self, view_name=None, urlvars_by_view_name=None, **kwargs):
        super(HyperlinkedNestedRelatedField, self).__init__(
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
        field_kwargs['view_name'] = self.Meta.resource_name + '-detail'
        field_kwargs['urlvars_by_view_name'] = self.Meta.urlvars_by_view_name

        return field_class, field_kwargs
