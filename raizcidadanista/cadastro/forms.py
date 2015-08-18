# -*- coding: utf-8 -*-
from django import forms

from models import Pessoa, Membro


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = ('nome', 'email', 'uf', 'municipio', 'sexo', )

class MembroForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('nome', 'uf', 'municipio', 'email', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento', 'rg', 'titulo_eleitoral',
            'uf_eleitoral', 'municipio_eleitoral', 'filiacao_partidaria', )

class FiliadoForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('nome', 'uf', 'municipio', 'email', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento', 'rg', 'titulo_eleitoral',
            'uf_eleitoral', 'municipio_eleitoral', 'filiacao_partidaria', )
