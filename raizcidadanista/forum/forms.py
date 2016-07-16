# -*- coding:utf-8 -*-
from django import forms
from django.contrib.auth.models import User

from ckeditor.widgets import CKEditorWidget
from forum.models import Grupo, Topico, Conversa, GrupoUsuario, ConversaMencao, GrupoCategoria


class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ('nome', 'descricao', )
        widgets = {
            'descricao': CKEditorWidget(config_name='basic'),
        }


class AddTopicoForm(forms.ModelForm):
    class Meta:
        model = Topico
        fields = ('titulo', 'categoria', )

    texto = forms.CharField(label=u'Descrição', widget=CKEditorWidget(config_name='basic'))
    categoria = forms.ModelChoiceField(label=u'Categoria', queryset=GrupoCategoria.objects.all())

    def __init__(self, grupo, *args, **kwargs):
        super(AddTopicoForm, self).__init__(*args, **kwargs)
        self.fields['categoria'].queryset = grupo.grupocategoria_set.all()

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


class PesquisaForm(forms.Form):

    texto = forms.CharField(required=False)
    autor = forms.CharField(required=False)
    grupo = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(PesquisaForm, self).clean()
        texto = cleaned_data.get('texto')
        autor = cleaned_data.get('autor')
        grupo = cleaned_data.get('grupo')
        if not (texto or autor or grupo):
            raise forms.ValidationError(u'Preencha pelo menos um campo.')
        return cleaned_data


class MencaoForm(forms.ModelForm):
    class Meta:
        model = ConversaMencao
        fields = ('conversa', )

    mencoes = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple, queryset=User.objects.all())