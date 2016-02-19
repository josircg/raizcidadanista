# -*- coding:utf-8 -*-
from django import forms

from forum.models import Topico


class AddTopicoForm(forms.ModelForm):
    class Meta:
        model = Topico
        fields = ('titulo', )