from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import HyperlinkedModelSerializer


class HyperlinkedNestedRelatedField(HyperlinkedRelatedField):

    def __init__(self, view_name=None, urlvars_by_resource_name=None, **kwargs):
        super(HyperlinkedNestedRelatedField, self).__init__(view_name, **kwargs)
        self.urlvars_by_resource_name = urlvars_by_resource_name or {}

    def get_url(self, obj, view_name, request, format):
        if obj.pk is None:
            return None

        current_view_kwargs = request.parser_context['kwargs']

        view_route_name = view_name.partition('-')[0]
        view_urlvars = self.urlvars_by_resource_name[view_route_name]

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

    def __init__(self, view_name=None, urlvars_by_resource_name=None, **kwargs):
        super(HyperlinkedNestedIdentityField, self) \
            .__init__(view_name, **kwargs)
        self.urlvars_by_resource_name = urlvars_by_resource_name or {}

    def get_url(self, obj, view_name, request, format):
        if obj.pk is None:
            return None

        current_view_kwargs = request.parser_context['kwargs']

        kwargs = {self.lookup_url_kwarg: getattr(obj, self.lookup_field)}
        kwargs.update(current_view_kwargs)
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
        super_ = super(HyperlinkedNestedModelSerializer, self)
        field_class, field_kwargs = \
            super_.build_url_field(field_name, model_class)
        field_kwargs['urlvars_by_resource_name'] = self.urlvars_by_resource_name
        return field_class, field_kwargs
