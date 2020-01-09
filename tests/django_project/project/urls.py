from django.conf.urls import url
from django.urls import include

urlpatterns = [
    url('', include('django_project.languages.urls')),
]
