# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.views.generic import TemplateView

from core import views

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='site/index.html'), name="index"),
    url(r'^membro/$', views.MembroView.as_view(), name="membro"),
    url(r'^membro-fundador/$', views.MembroFundadorView.as_view(), name="membro-fundador"),
]
