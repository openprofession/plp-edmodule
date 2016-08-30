# coding: utf-8

from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^edmodule-enroll/?$', views.edmodule_enroll, name='edmodule-enroll'),
    url(r'^edmodule/(?P<code>[-\w]+)/?$', views.module_page, name='edmodule-page'),
    url(r'^get-honor-text/?$', views.get_honor_text, name='get-honor-text'),
    url(r'^course/filter/?$', views.edmodule_filter_view, name='edmodule-filter'),
]
