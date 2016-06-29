# -*- coding: utf-8 -*-
from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^caixa/$', CaixaView.as_view(), name='financeiro_caixa'),
]