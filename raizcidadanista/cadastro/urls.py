# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from cadastro import views

urlpatterns = [
    # url(r'^newsletter/$', views.NewsletterView.as_view(), name="newsletter"),
    # url(r'^membro/$', views.MembroView.as_view(), name="membro"),
    # url(r'^membro/entrar-circulo/(?P<circulo_id>\d+)/$', login_required(views.MembroEntrarCirculoView.as_view()), name="membro_entrar_circulo"),
    # url(r'^filiado/$', views.FiliadoView.as_view(), name="filiado"),
    # url(r'^atualizar-cadastro/$', views.AtualizarCadastroLinkView.as_view(), name="atualizar_cadastro_link"),
    # url(r'^atualizar-cadastro/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<ts_b36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,20})/$', views.AtualizarCadastroView.as_view(), name="atualizar_cadastro"),
    # url(r'^validar-email/(?P<pessoa_id>\d+)/$', views.ValidarEmailView.as_view(), name="validar_email"),
    # url(r'^campanha/(?P<pk>\d+)/$', views.CampanhaView.as_view(), name='campanha_views'),
]
