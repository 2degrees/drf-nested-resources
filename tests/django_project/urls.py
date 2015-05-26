from tests.django_project.app.views import view

from django.conf.urls import url


urlpatterns = (
    url(r'^parent/(?P<parent_id>\w+)/children/$', view, name='children'),
    url(r'^parent/(?P<parent_id>\w+)/children/(?P<pk>\w+)/$', view, name='child'),
    url(r'^parent/(?P<parent_id>\w+)/children/(?P<pk>\w+)\.(?P<format>\w+)$', view, name='child'),
    )
