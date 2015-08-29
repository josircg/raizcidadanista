# -*- coding: utf-8 -*-
from django import forms
from django.contrib.localflavor.br.forms import BRCPFField
from models import Pessoa, Membro


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = ('nome', 'email', 'uf', 'municipio', )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Pessoa.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email. Se você já é colaborador ou filiado, você já irá receber os nossos informes.')
        return email

class MembroForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('nome', 'email', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'filiacao_partidaria',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email. Faça login no site para que possa alterar seus dados.')
        return email


class FiliadoForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('nome', 'email', 'cpf', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento',
            'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral', 'zona_eleitoral', 'secao_eleitoral', 'nome_da_mae', )

    cpf = BRCPFField(
        label='CPF',
        error_messages={
            'invalid':u'Preencha corretamente o seu CPF.',
            'max_digits': u'Certifique-se de que o valor tenha no máximo 11 números no formato: XXX.XXX.XXX-XX.',
            'digits_only': u'Preencha apenas com números, ou no formato: XXX.XXX.XXX-XX.',
        }
    )

    def __init__(self, *args, **kwargs):
        super(FiliadoForm, self).__init__(*args, **kwargs)
        self.fields['nome_da_mae'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email. Faça login no site para que possa alterar seus dados.')
        return email

    def save(self, commit=True):
        self.instance.filiado = True
        return super(FiliadoForm, self).save(commit)
