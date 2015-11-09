# -*- coding: utf-8 -*-
from django.contrib import admin

from poweradmin.admin import PowerModelAdmin, PowerButton

from models import Conta, Receita


class ContaAdmin(PowerModelAdmin):
    list_display = ('conta', 'descricao', 'tipo', 'ativa', )
    list_filter = ('tipo', 'ativa', )
    search_fields = ['conta', 'descricao',]
    multi_search = (
        ('q1', u'Conta', ['conta', ]),
        ('q2', u'Descrição', ['descricao', ]),
    )

    fieldsets = [
        (None, {'fields': ('conta', 'descricao', 'tipo', 'ativa',)}),
        (u'Detalhes', {'fields': ('nota', )}),
    ]
admin.site.register(Conta, ContaAdmin)


class ReceitaAdmin(PowerModelAdmin):
    list_display = ('conta', 'colaborador', 'dtaviso', 'valor', 'dtpgto',  )
    list_filter = ('conta', 'dtaviso', 'dtpgto', )
    search_fields = ['conta', 'descricao', ]
    raw_id_fields = ('colaborador', )
    multi_search = (
        ('q1', u'Conta', ['conta__conta', ]),
        ('q2', u'Colaborador', ['colaborador__nome', ]),
    )

    fieldsets = [
        (None, {'fields': ('conta', 'colaborador', )}),
        (u'Datas e Valor', {'fields': ('dtaviso', 'valor', 'dtpgto', )}),
    ]
admin.site.register(Receita, ReceitaAdmin)