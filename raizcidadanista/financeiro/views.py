# -*- coding: utf-8 -*-
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.db.models import Sum

from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from decimal import Decimal

from utils.stdlib import normalizar_data
from models import Operacao, PeriodoContabil, Receita, TipoDespesa, Pagamento
from forms import CaixaForm


class CaixaView(TemplateView):
    template_name = 'admin/financeiro/caixa.html'
    form_class = CaixaForm

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('auth.view_caixa'):
            raise PermissionDenied()

        saldo_inicial = saldo_final = Decimal(0)
        operacoes = operacoes_saldo_inicial = []
        depositos_despesas = {}
        #Transferencias
        transferencias = {}
        #Total de receitas
        total_receitas = Decimal(0)
        step = 1

        form = self.form_class()
        if request.GET.get('action'):
            GET = request.GET.copy()
            GET['dt_inicial'] = normalizar_data(GET['dt_inicial'])
            GET['dt_final'] = normalizar_data(GET['dt_final'])
            form = self.form_class(GET)
            if form.is_valid():
                step = 2

                dt_inicial = form.cleaned_data.get('dt_inicial')
                dt_final = form.cleaned_data.get('dt_final')
                if not dt_final or dt_final < dt_inicial:
                    return HttpResponseRedirect("%s?action=search&dt_inicial=%s&dt_final=%s&conta=%s" % (
                        reverse('convenio_caixa'),
                        dt_inicial.strftime('%d/%m/%Y'),
                        dt_inicial.strftime('%d/%m/%Y'),
                        form.cleaned_data.get('conta').pk
                    ))

                #Pega todas as operações
                operacoes_root = Operacao.objects.filter(conta=form.cleaned_data.get('conta'))

                #Pega as operações pela data
                operacoes = operacoes_root.filter(dt__gte=dt_inicial, dt__lte=dt_final).exclude(tipo='S').order_by('dt', 'id')

                #Tenta encontrar o Saldo inicial Fixo
                try:
                    ultimo_saldo = operacoes_root.filter(dt__lte=dt_inicial, tipo='S').order_by('-dt').latest('dt')
                    saldo_inicial = operacoes_root.get(dt=ultimo_saldo.dt, tipo = 'S').valor
                    ultimo_saldo = ultimo_saldo.dt
                except:
                    ultimo_saldo = datetime(2000,1,1)
                    saldo_inicial = Decimal(0)

                # operações que estiverem entre o último saldo e a data inicial devem ser incluídas
                # no saldo inicial
                saldo_inicial += operacoes_root.filter(dt__gte=ultimo_saldo, dt__lt=dt_inicial).exclude(tipo='S').aggregate(Sum('valor'))['valor__sum'] or Decimal(0)

                #Calcula o Saldo Final e o total das demais operações
                saldo_final = saldo_inicial
                for operacao in operacoes:
                    saldo_final += operacao.valor
                    operacao.total_caixa = saldo_final

        return render_to_response(self.template_name, {
            'title': u'Caixa',
            'form': form,
            'step': step,
            'saldo_inicial': saldo_inicial,
            'saldo_final': saldo_final,
            'operacoes': operacoes,
            'operacoes_saldo_inicial': operacoes_saldo_inicial,
        },context_instance=RequestContext(request))


class CaixaPeriodoView(DetailView):
    template_name = 'financeiro/caixa-periodo.html'
    model = PeriodoContabil
    slug_field = 'ciclo'
    slug_url_kwarg = 'ciclo'

    def get_context_data(self, **kwargs):
        context = super(CaixaPeriodoView, self).get_context_data(**kwargs)
        if not self.object.publico:
            return context

        dt_inicial = date(day=1, month=self.object.month(), year=self.object.year())
        dt_final = dt_inicial+relativedelta(months=1)
        #Pega todas as operações
        operacoes_root = Operacao.objects.all()
        #Pega as operações pela data
        operacoes = operacoes_root.filter(dt__gte=dt_inicial, dt__lt=dt_final).exclude(tipo='S').order_by('dt', 'id')
        #Tenta encontrar o Saldo inicial Fixo
        try:
            ultimo_saldo = operacoes_root.filter(dt__lte=dt_inicial, tipo='S').order_by('-dt').latest('dt')
            saldo_inicial = operacoes_root.get(dt=ultimo_saldo.dt, tipo = 'S').valor
            ultimo_saldo = ultimo_saldo.dt
        except:
            ultimo_saldo = datetime(2000,1,1)
            saldo_inicial = Decimal(0)

        # Operações que estiverem entre o último saldo e a data inicial devem ser incluídas no saldo inicial
        saldo_inicial += operacoes_root.filter(dt__gte=ultimo_saldo, dt__lt=dt_inicial).exclude(tipo='S').aggregate(Sum('valor'))['valor__sum'] or Decimal(0)

        # Calcula o total de receitas
        total_receitas = Operacao.objects.filter(dt__gte=dt_inicial, dt__lt=dt_final, tipo='D').aggregate(Sum('valor'))['valor__sum'] or Decimal(0)

        # Agrupa os Pagamentos por Tipo de Despesa
        total_pagamentos = Decimal(0)
        pagamentos = []
        for tipo in TipoDespesa.objects.all():
            total = abs(Pagamento.objects.filter(dt__gte=dt_inicial, dt__lt=dt_final, tipo_despesa=tipo).aggregate(Sum('valor'))['valor__sum'] or Decimal(0))
            total_pagamentos += total
            pagamentos.append({
                'tipo': tipo,
                'total': total
            })
        # Pagamento sem tipo_despesa
        total = abs(Pagamento.objects.filter(dt__gte=dt_inicial, dt__lt=dt_final, tipo_despesa=None).aggregate(Sum('valor'))['valor__sum'] or Decimal(0))
        total_pagamentos += total
        pagamentos.append({
            'tipo': u'Outras',
            'total': total
        })

        #Calcula o Saldo Final
        saldo_final = saldo_inicial+total_receitas-total_pagamentos

        context['saldo_inicial'] = saldo_inicial
        context['total_receitas'] = total_receitas
        context['pagamentos'] = pagamentos
        context['saldo_final'] = saldo_final
        return context


class CaixaDetalhePeriodoView(DetailView):
    template_name = 'financeiro/caixa-detalhe-periodo.html'
    model = PeriodoContabil
    slug_field = 'ciclo'
    slug_url_kwarg = 'ciclo'

    def get_context_data(self, **kwargs):
        context = super(CaixaDetalhePeriodoView, self).get_context_data(**kwargs)
        if not self.object.publico:
            return context

        dt_inicial = date(day=1, month=self.object.month(), year=self.object.year())
        dt_final = dt_inicial+relativedelta(months=1)
        #Pega todas as operações
        operacoes_root = Operacao.objects.all()
        #Pega as operações pela data
        operacoes = operacoes_root.filter(dt__gte=dt_inicial, dt__lt=dt_final).exclude(tipo__in=('S', 'T' )).order_by('dt', 'id')
        #Tenta encontrar o Saldo inicial Fixo
        try:
            ultimo_saldo = operacoes_root.filter(dt__lte=dt_inicial, tipo='S').order_by('-dt').latest('dt')
            saldo_inicial = operacoes_root.get(dt=ultimo_saldo.dt, tipo='S').valor
            ultimo_saldo = ultimo_saldo.dt
        except:
            ultimo_saldo = datetime(2000,1,1)
            saldo_inicial = Decimal(0)

        # Operações que estiverem entre o último saldo e a data inicial devem ser incluídas no saldo inicial
        saldo_inicial += operacoes_root.filter(dt__gte=ultimo_saldo, dt__lt=dt_inicial).exclude(tipo='S').aggregate(Sum('valor'))['valor__sum'] or Decimal(0)

        #Calcula o Saldo Final e o total das demais operações
        saldo_final = saldo_inicial
        for operacao in operacoes:
            saldo_final += operacao.valor
            operacao.total_caixa = saldo_final

        context['saldo_inicial'] = saldo_inicial
        context['operacoes'] = operacoes
        context['saldo_final'] = saldo_final
        return context