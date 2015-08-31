# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.views.generic import TemplateView

from cadastro import views

urlpatterns = [
    url(r'^newsletter/$', views.NewsletterView.as_view(), name="newsletter"),
    url(r'^membro/$', views.MembroView.as_view(), name="membro"),
    url(r'^filiado/$', views.FiliadoView.as_view(), name="filiado"),
    url(r'^filiado/atualizar/$', views.FiliadoAtualizarLinkView.as_view(), name="filiado_atualizar_link"),
    url(r'^filiado/atualizar/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,20})/$', views.FiliadoAtualizarView.as_view(), name="filiado_atualizar"),
]
