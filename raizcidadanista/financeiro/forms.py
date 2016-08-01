# -*- coding: utf-8 -*-
from django import forms
from django.contrib.admin.widgets import AdminRadioSelect, AdminDateWidget
from django.contrib.localflavor.br.forms import BRCNPJField, BRCPFField

from models import Fornecedor, Conta, Orcamento, PeriodoContabil

from datetime import date


class FornecedorAdminForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ('nome', 'identificador', 'dados_financeiros', 'servico_padrao', 'ativo', )

    TIPO_CHOICES = (
        ('PF', u'Pessoa Física'),
        ('PJ', u'Pessoa Jurídica'),
    )
    tipo = forms.ChoiceField(widget=AdminRadioSelect(attrs={'class': 'radiolist inline'}), choices=TIPO_CHOICES, initial='PJ')
    identificador = forms.CharField(label=u'CPF/CNPJ', max_length=18)

    def _only_numbers(self, value):
        return ''.join(val for val in value if val.isdigit())

    def clean_identificador(self):
        return self._only_numbers(self.cleaned_data.get('identificador'))

    def __init__(self, *args, **kwargs):
        super(FornecedorAdminForm, self).__init__(*args, **kwargs)
        identificador = self._only_numbers(self.instance.identificador)
        if args and args[0].get('identificador'):
            identificador = self._only_numbers(args[0].get('identificador'))

        if identificador:
            self.fields['tipo'].initial = 'PF' if len(identificador) == 11 else 'PJ'

        if self.fields['tipo'].initial == 'PF':
            self.fields['identificador'] = BRCPFField(label=u'CPF/CNPJ')
        else:
            self.fields['identificador'] = BRCNPJField(label=u'CPF/CNPJ')


class CaixaForm(forms.Form):
    dt_inicial = forms.DateField(label=u'Data inicial', widget=AdminDateWidget())
    dt_final = forms.DateField(label=u'Data final', required=False, widget=AdminDateWidget())
    conta = forms.ModelChoiceField(label=u"Conta", queryset=Conta.objects.all())


class OrcamentoAdminForm(forms.ModelForm):
    class Meta:
        model = Orcamento

    repetir = forms.CharField(label=u'Periodo final', required=False, max_length=6, help_text=u'Informe um período, ex.: 201701')
    editar_filhos = forms.BooleanField(required=False)#, widget=forms.HiddenInput())

    def clean_repetir(self):
        repetir = self.cleaned_data.get('repetir')
        periodo = self.cleaned_data.get('periodo')
        if repetir and periodo:
            repetir_date = date(day=1, month=int(repetir[-2:]), year=int(repetir[:4]))
            periodo_date = date(day=1, month=periodo.month(), year=periodo.year())
            if periodo_date >= repetir_date:
                raise forms.ValidationError(u'Informe um período superior a %s' % periodo)
        return repetir

    def clean_periodo_final(self):
        periodo_final = self.cleaned_data.get('periodo_final')
        periodo = self.cleaned_data.get('periodo')
        if periodo_final and periodo:
            periodo_final_date = date(day=1, month=periodo_final.month(), year=periodo_final.year())
            periodo_date = date(day=1, month=periodo.month(), year=periodo.year())
            if periodo_date >= periodo_final_date:
                raise forms.ValidationError(u'Informe um período superior a %s' % periodo)
        return periodo_final