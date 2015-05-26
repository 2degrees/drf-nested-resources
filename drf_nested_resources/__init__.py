from rest_framework.relations import HyperlinkedIdentityField


class HyperlinkedNestedIdentityField(HyperlinkedIdentityField):

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

