from tests.django_project.app.views import view

from django.conf.urls import url


urlpatterns = (
    url(r'^parents/(?P<parent>\w+)/children/$', view, name='children'),
    url(r'^parents/(?P<parent>\w+)/children/(?P<child>\w+)/$', view, name='child'),
    url(r'^parents/(?P<parent>\w+)/children/(?P<child>\w+)\.(?P<format>\w+)$', view, name='child'),
)
