# -*- coding: utf-8 -*-
from django.contrib import admin
from django.template.loader import get_template
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.http import HttpResponse
from django.db import models
from django import forms
from django.db.models import Sum

import cStringIO as StringIO
import cgi
from xhtml2pdf.pisa import pisaDocument

from poweradmin.admin import PowerModelAdmin, PowerButton

from forms import FornecedorAdminForm
from models import PeriodoContabil, Conta, ContaContabil, Projeto, TipoDespesa, Fornecedor, Operacao, Pagamento, Despesa, Transferencia, \
    Deposito, Receita, MetaArrecadacao, Orcamento


class PeriodoContabilAdmin(PowerModelAdmin):
    list_display = ('ciclo', 'status', 'publico', )
    search_fields = ('ciclo', )
    fieldsets = [
        (None, {'fields': ('ciclo', ('status', 'publico', ), )}),
    ]
    def get_buttons(self, request, object_id):
        buttons = super(PeriodoContabilAdmin, self).get_buttons(request, object_id)
        obj = self.get_object(request, object_id)
        if obj and obj.publico:
            buttons.append(PowerButton(url=reverse('financeiro_caixa_periodo', kwargs={'ciclo': obj.ciclo}), label='Caixa'))
        return buttons
admin.site.register(PeriodoContabil, PeriodoContabilAdmin)

class ContaContabilAdmin(PowerModelAdmin):
    list_display = ('codigo', 'descricao', 'ordem_sped', 'tipo_sped' )
    multi_search = (
        ('q1', u'Código', ['codigo', ]),
        ('q2', u'Descrição', ['descricao', ]),
    )
admin.site.register(ContaContabil, ContaContabilAdmin)

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


class TipoDespesaAdmin(PowerModelAdmin):
    list_display = ('codigo', 'descricao_breve', )
    multi_search = (
        ('q1', u'Código', ['codigo', 'descricao_breve',]),
        ('q2', u'Descrição', [ 'descricao', ]),
    )
    fieldsets = (
        (None, {'fields': ('codigo', 'descricao_breve', 'descricao', ),}),
    )
admin.site.register(TipoDespesa, TipoDespesaAdmin)


class PagamentoProjetoInline(admin.TabularInline):
    model = Pagamento
    extra = max_num = 0
    fields = ('dt', 'valor', 'referencia')
    readonly_fields = ('dt', 'valor', 'referencia')
    fields = ('pagamento_link', 'dt', 'valor', 'referencia', )
    readonly_fields = ('pagamento_link', 'valor')

    def pagamento_link(self, obj):
        return u'<a href="%s">%s</a>' % (reverse('admin:financeiro_pagamento_change', args=(obj.pk, )), obj)
    pagamento_link.allow_tags = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class ProjetoAdmin(PowerModelAdmin):
    list_display = ('nome', 'orcamento', 'responsavel', 'ativo')
    multi_search = (
        ('q1', u'nome', ['nome',]),
    )
    fieldsets = (
        (None, {'fields': ('nome', 'descricao', 'orcamento', 'dtinicio', 'dtfim',
                           'responsavel', 'ativo'),}),
    )
    inlines = (PagamentoProjetoInline, )

admin.site.register(Projeto, ProjetoAdmin)


class FornecedorAdmin(PowerModelAdmin):
    list_display = ('nome', 'identificador', 'ativo', )
    list_filter = ('ativo', )
    multi_search = (
        ('q1', u'Nome', ['nome', ]),
        ('q2', u'CPF/CNPJ', ['identificador', ]),
    )
    fieldsets = (
        (None, {'fields': ('nome', 'tipo', 'identificador', 'dados_financeiros', 'servico_padrao', 'ativo', ),}),
    )
    form = FornecedorAdminForm
admin.site.register(Fornecedor, FornecedorAdmin)


class PagamentoDespesaInline(admin.TabularInline):
    model = Pagamento
    extra = max_num = 0
    fields = ('referencia', 'dt', 'valor')
    readonly_fields = ('valor', )
    fields = ('pagamento_link', 'referencia', 'dt', 'valor')
    readonly_fields = ('pagamento_link', 'valor')

    def pagamento_link(self, obj):
        return u'<a href="%s">%s</a>' % (reverse('admin:financeiro_pagamento_change', args=(obj.pk, )), obj)
    pagamento_link.allow_tags = True

class DespesaAdmin(PowerModelAdmin):
    list_display = ('fornecedor', 'tipo_despesa', 'dtemissao', 'dtvencimento', 'valor', )
    list_filter = ('tipo_despesa', 'integral',)
    date_hierarchy = 'dtemissao'
    multi_search = (
        ('q1', u'Fornecedor', ['fornecedor__nome', ]),
    )
    fieldsets = (
        (None, {'fields': ('fornecedor', 'tipo_despesa', ('dtemissao', 'dtvencimento',), 'documento', 'valor', 'saldo_a_pagar', 'integral', ),}),
        (None, {'fields': ('observacoes', ),}),
    )
    readonly_fields = ('saldo_a_pagar', )
    formfield_overrides = {
        models.DecimalField: {'localize': True},
    }
    inlines = (PagamentoDespesaInline, )
admin.site.register(Despesa, DespesaAdmin)


class OperacaoAdmin(PowerModelAdmin):
    list_display = ('conta', 'tipo', 'dt', 'referencia', 'valor', 'conferido',)
    list_filter = ('conta', 'tipo', 'conferido', )
    date_hierarchy = 'dt'
    multi_search = (
        ('q1', u'Conta', ['conta__conta', ]),
        ('q2', u'Referência', ['referencia', ]),
    )
    fieldsets = (
        (None, {'fields': ('conta', 'tipo', 'dt', 'referencia', 'valor', 'conferido', 'obs', ),}),
    )
    formfield_overrides = {
        models.DecimalField: {'localize': True},
    }

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "tipo":
            kwargs['choices'] = (
                ('', u'--------'),
                ('F', u'Rendimentos Financeiros'),
                ('Q', u'Restituição'),
                ('S', u'Saldo'),
            )
        return super(OperacaoAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)
admin.site.register(Operacao, OperacaoAdmin)


class PagamentoAdmin(PowerModelAdmin):
    list_display = ('conta', 'dt', 'despesa', 'tipo_despesa', 'fornecedor', 'referencia', 'valor', 'conferido',)
    list_filter = ('fornecedor', 'conta', 'tipo', 'conferido', )
    date_hierarchy = 'dt'
    multi_search = (
        ('q1', u'Fornecedor', ['fornecedor__nome', ]),
        ('q2', u'Referência', ['referencia', ]),
    )
    fieldsets = (
        (None, {'fields': ('conta', 'dt', 'fornecedor', 'despesa', 'tipo_despesa', 'projeto', 'referencia', 'valor', 'comprovante', 'conferido', 'obs', ),}),
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


class DepositoAdmin(PowerModelAdmin):
    list_display = ('conta', 'receita', 'tipo', 'dt', 'referencia', 'valor', 'conferido',)
    list_filter = ('conta', 'tipo', 'conferido', )
    date_hierarchy = 'dt'
    multi_search = (
        ('q1', u'Referência', ['referencia', ]),
    )
    fieldsets = (
        (None, {'fields': ('conta', 'receita', 'dt', 'referencia', 'valor', 'conferido', 'obs', ),}),
    )
    def save_model(self, request, obj, form, change):
        obj.tipo = 'D'
        return super(DepositoAdmin, self).save_model(request, obj, form, change)
admin.site.register(Deposito, DepositoAdmin)


class ReceitaAdmin(PowerModelAdmin):
    list_display = ('conta', 'colaborador', 'dtaviso', 'valor', 'dtpgto',  )
    list_filter = ('conta', 'colaborador__uf', 'dtaviso', 'dtpgto', )
    search_fields = ['conta', 'descricao', ]
    raw_id_fields = ('colaborador', )
    multi_search = (
        ('q1', u'Conta', ['conta__conta', ]),
        ('q2', u'Colaborador', ['colaborador__nome', ]),
    )
    fieldsets = [
        (None, {'fields': ('conta', 'colaborador', )}),
        (u'Datas e Valor', {'fields': ('dtaviso', 'valor', 'dtpgto', )}),
        (u'Detalhes', {'fields': ('nota', )}),
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

class OrcamentoAdmin(PowerModelAdmin):
    list_filter = ( 'tipo_despesa', 'periodo', )
    list_display = ('periodo', 'tipo_despesa', 'valor', 'realizado')
    fields = ('periodo', 'periodo_final', 'tipo_despesa', 'valor')

admin.site.register(Orcamento, OrcamentoAdmin)
