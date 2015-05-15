# -*- coding: utf-8 -*-
from django import forms

from models import Membro


class MembroForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('nome', 'email', 'sexo', )