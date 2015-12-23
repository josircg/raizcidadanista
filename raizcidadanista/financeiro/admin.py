# -*- coding: utf-8 -*-
from django.contrib import admin
from django.template.loader import get_template
from django.template.context import RequestContext
from django.http import HttpResponse
from django.db.models import Sum

import cStringIO as StringIO
import cgi
from xhtml2pdf.pisa import pisaDocument

from poweradmin.admin import PowerModelAdmin, PowerButton

from models import Conta, Receita, MetaArrecadacao


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
    actions = ('listagem_doadores', )

    def listagem_doadores(self, request, queryset, template_name_pdf='admin/financeiro/receita/listagem-doadores-pdf.html'):
        template = get_template(template_name_pdf)
        context = RequestContext(request, {
            'results': queryset,
            'total': queryset.aggregate(total=Sum('valor')).get('total', 0)
        })
        html  = template.render(context)

        dataresult = StringIO.StringIO()
        pdf = pisaDocument(StringIO.StringIO(html.encode("UTF-8")), dest=dataresult)
        if not pdf.err:
            return HttpResponse(dataresult.getvalue(), mimetype='application/pdf')
        return HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))
    listagem_doadores.short_description = u'Listagem Doadores'
admin.site.register(Receita, ReceitaAdmin)


class MetaArrecadacaoAdmin(PowerModelAdmin):
    list_display = ('descricao', 'data_inicial', 'data_limite', 'valor', )
    list_filter = ( 'data_inicial', 'data_limite', )
    search_fields = ['descricao', ]
    fieldsets = [
        (None, {'fields': ('descricao', )}),
        (u'Datas e Valor', {'fields': ('data_inicial', 'data_limite', 'valor', )}),
    ]
admin.site.register(MetaArrecadacao, MetaArrecadacaoAdmin)