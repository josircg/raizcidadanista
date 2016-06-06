# -*- coding:utf-8 -*-
from django import forms

from ckeditor.widgets import CKEditorWidget
from forum.models import Topico, Conversa


class AddTopicoForm(forms.ModelForm):
    class Meta:
        model = Topico
        fields = ('titulo', )

    texto = forms.CharField(label=u'Descrição', widget=CKEditorWidget(config_name='basic'))

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
        return topico


class ConversaForm(forms.ModelForm):
    class Meta:
        model = Conversa
        fields = ('texto', 'conversa_pai', )
        widgets = {
            'texto': CKEditorWidget(config_name='basic'),
            'conversa_pai': forms.HiddenInput(),
        }

    def save(self, topico, autor, *args, **kwargs):
        self.instance.topico = topico
        self.instance.autor = autor
        return super(ConversaForm, self).save(*args, **kwargs)