# -*- coding: utf-8 -*-
from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^caixa/$', CaixaView.as_view(), name='financeiro_caixa'),
    url(r'^caixa/(?P<ciclo>\d{6})/$', CaixaPeriodoView.as_view(), name='financeiro_caixa_periodo'),
    url(r'^caixa-detalhe/(?P<ciclo>\d{6})/$', CaixaDetalhePeriodoView.as_view(), name='financeiro_caixa_detalhe_periodo'),
    url(r'^planejamento-orcamentario/(?P<ano>\d{4})?/?$', PlanejamentoOrcamentarioView.as_view(), name='financeiro_planejamento_orcamentario'),
]