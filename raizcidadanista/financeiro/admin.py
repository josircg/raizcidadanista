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

from models import PeriodoContabil, Conta, Operacao, ReceitaOperacao, MetaArrecadacao



class PeriodoContabilAdmin(PowerModelAdmin):
    list_display = ('ciclo', 'status', )
    search_fields = ('ciclo', )
    fieldsets = [
        (None, {'fields': ('ciclo', 'status', )}),
    ]
admin.site.register(PeriodoContabil, PeriodoContabilAdmin)


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


class OperacaoAdmin(PowerModelAdmin):
    list_display = ('conta', 'tipo', 'dt', 'referencia', 'valor', 'conferido',)
    list_filter = ('conta', 'tipo', 'conferido', )
    date_hierarchy = 'dt'
    multi_search = (
        ('q1', u'Conta', ['conta__conta', ]),
        ('q2', u'Referência', ['referencia', ]),
        ('q3', u'Convenente', ['conta__convenente__nome', ]),
    )
    fieldsets = (
        (None, {'fields': ('conta', 'tipo', 'dt', 'referencia', 'valor', 'conferido', 'obs', ),}),
    )
    formfield_overrides = {
        models.DecimalField: {'localize': True},
    }
admin.site.register(Operacao, OperacaoAdmin)


class PagamentoAdmin(PowerModelAdmin):
    list_display = ('conta', 'colaborador', 'despesa_display', 'dt', 'referencia', 'valor', 'conferido',)
    list_filter = ('colaborador', 'conta', 'tipo', 'conferido', )
    date_hierarchy = 'dt'
    multi_search = (
        ('q1', u'Colaborador', ['colaborador__nome', ]),
        ('q2', u'Referência', ['referencia', ]),
    )
    fieldsets = (
        (None, {'fields': ('conta', 'colaborador', 'dt', 'referencia', 'valor', 'conferido', 'obs', ),}),
    )
    formfield_overrides = {
        models.DecimalField: {'localize': True},
    }
admin.site.register(Pagamento, PagamentoAdmin)



class TransferenciaAdmin(PowerModelAdmin):
    list_display = ('conta', 'destino', 'tipo', 'dt', 'referencia', 'valor', 'conferido',)
    list_filter = ('conta', 'tipo', 'conferido', )
    readonly_fields = ('transf_associada_display', )
    date_hierarchy = 'dt'
    multi_search = (
        ('q1', u'Referência', ['referencia', ]),
    )
    fieldsets = (
        (None, {'fields': ('conta', 'destino', 'transf_associada_display', 'dt', 'referencia', 'valor', 'conferido', 'obs', ),}),
    )
    def save_model(self, request, obj, form, change):
        obj.tipo = 'T'
        return super(TransferenciaAdmin, self).save_model(request, obj, form, change)
admin.site.register(Transferencia, TransferenciaAdmin)


class ReceitaOperacaoAdmin(PowerModelAdmin):
    list_display = ('conta', 'colaborador', 'dt', 'valor', 'dtpgto',  )
    list_filter = ('conta', 'colaborador__uf', 'dt', 'dtpgto', )
    search_fields = ['conta', 'descricao', ]
    raw_id_fields = ('colaborador', )
    multi_search = (
        ('q1', u'Conta', ['conta__conta', ]),
        ('q2', u'Colaborador', ['colaborador__nome', ]),
    )
    fieldsets = [
        (None, {'fields': ('conta', 'colaborador', )}),
        (u'Datas e Valor', {'fields': ('dt', 'valor', 'dtpgto', 'conferido', )}),
        (u'Detalhes', {'fields': ('referencia', 'obs', )}),
    ]
    actions = ('listagem_doadores', )

    def save_model(self, request, obj, form, change):
        obj.tipo = 'D'
        return super(ReceitaOperacaoAdmin, self).save_model(request, obj, form, change)

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
admin.site.register(ReceitaOperacao, ReceitaOperacaoAdmin)


class MetaArrecadacaoAdmin(PowerModelAdmin):
    list_display = ('descricao', 'data_inicial', 'data_limite', 'valor', )
    list_filter = ( 'data_inicial', 'data_limite', )
    search_fields = ['descricao', ]
    fieldsets = [
        (None, {'fields': ('descricao', )}),
        (u'Datas e Valor', {'fields': ('data_inicial', 'data_limite', 'valor', )}),
    ]
admin.site.register(MetaArrecadacao, MetaArrecadacaoAdmin)