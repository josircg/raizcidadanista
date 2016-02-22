# -*- coding:utf-8 -*-
from django import forms

from forum.models import Topico, Conversa


class AddTopicoForm(forms.ModelForm):
    class Meta:
        model = Topico
        fields = ('titulo', )

    texto = forms.CharField(label=u'Descrição', widget=forms.Textarea)


    def save(self, grupo, criador, *args, **kwargs):
        self.instance.grupo = grupo
        self.instance.criador = criador

        topico = super(AddTopicoForm, self).save(*args, **kwargs)

        # Cria a Conversa com o texto informado pelo autor
        Conversa(
            topico=topico,
            autor=criador,
            texto=self.cleaned_data.get('texto'),
        ).save()