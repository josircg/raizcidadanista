# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from forum import views

urlpatterns = [
    url(r'^grupo/(?P<pk>\d+)/$', views.GrupoView.as_view(), name='forum_grupo'),
]
