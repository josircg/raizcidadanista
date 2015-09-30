# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from cadastro import views

urlpatterns = [
    url(r'^newsletter/$', views.NewsletterView.as_view(), name="newsletter"),
    url(r'^membro/$', views.MembroView.as_view(), name="membro"),
    url(r'^membro/entrar-circulo/(?P<circulo_id>\d+)/$', login_required(views.MembroEntrarCirculoView.as_view()), name="membro_entrar_circulo"),
    url(r'^filiado/$', views.FiliadoView.as_view(), name="filiado"),
    url(r'^filiado/atualizar/$', views.FiliadoAtualizarLinkView.as_view(), name="filiado_atualizar_link"),
    url(r'^filiado/atualizar/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,20})/$', views.FiliadoAtualizarView.as_view(), name="filiado_atualizar"),
    url(r'^validar-email/(?P<pessoa_id>\d+)/$', views.ValidarEmailView.as_view(), name="validar_email"),
    url(r'^campanha/(?P<pk>\d+)/$', views.CampanhaView.as_view(), name='campanha_views'),
]
