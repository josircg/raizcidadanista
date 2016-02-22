# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from forum import views

urlpatterns = [
    url(r'^$', login_required(views.ForumView.as_view()), name='forum'),
    url(r'^grupo/(?P<pk>\d+)/$', login_required(views.GrupoView.as_view()), name='forum_grupo'),
]
