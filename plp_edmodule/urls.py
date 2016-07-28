# coding: utf-8

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^edmodule-enroll/?$', views.edmodule_enroll, name='edmodule-enroll'),
]
