# -*- coding: utf-8 -*-
from django import forms

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
            'atividade_profissional', )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email. Faça login no site para que possa alterar seus dados.')
        return email


class FiliadoForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('nome', 'email', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento', 'titulo_eleitoral',
            'uf_eleitoral', 'municipio_eleitoral', 'zona_eleitoral', 'secao_eleitoral', 'filiacao_partidaria', )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email. Faça login no site para que possa alterar seus dados.')
        return email

    def save(self, commit=True):
        self.instance.filiado = True
        return super(FiliadoForm, self).save(commit)
