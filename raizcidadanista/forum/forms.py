# -*- coding:utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from ckeditor.widgets import CKEditorWidget
from forum.models import Grupo, Topico, Conversa, GrupoUsuario, ConversaMencao, GrupoCategoria, \
    Proposta, Voto
from utils.storage import save_file

from datetime import datetime

class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ('nome', 'privado', 'descricao', )
        widgets = {
            'descricao': CKEditorWidget(config_name='basic'),
        }


class AddEditTopicoForm(forms.ModelForm):
    class Meta:
        model = Topico
        fields = ('titulo',)

    texto = forms.CharField(label=u'Descrição', widget=CKEditorWidget(config_name='basicadd'))
    imagem = forms.ImageField(label=u'Imagem', required=False)
    arquivo = forms.FileField(label=u'Arquivo', required=False)
    categoria = forms.ModelChoiceField(label=u'Categoria', queryset=GrupoCategoria.objects.all(), required=False, help_text='Pode ficar em branco')

    def __init__(self, grupo, *args, **kwargs):
        super(AddEditTopicoForm, self).__init__(*args, **kwargs)
        if grupo.grupocategoria_set.count() > 0:
            self.fields['categoria'].queryset = grupo.grupocategoria_set.all()
            if kwargs.get('instance') and kwargs.get('instance').categoria:
                self.fields['categoria'].initial = kwargs.get('instance').categoria
        else:
            del self.fields['categoria']
        if kwargs.get('instance'):
            try:
                conversa = Conversa.objects.filter(topico=kwargs.get('instance'), conversa_pai=None)[0]
                self.fields['texto'].initial = conversa.texto
            except: pass


    def save(self, grupo, editor, *args, **kwargs):
        self.instance.grupo = grupo
        try:
            if not self.instance.criador:
                self.instance.criador = editor
        except ObjectDoesNotExist: self.instance.criador = editor
        self.instance.categoria = self.cleaned_data.get('categoria')
        topico = super(AddEditTopicoForm, self).save(*args, **kwargs)

        texto = self.cleaned_data.get('texto')
        if self.cleaned_data.get('imagem'):
            filename = save_file(self.cleaned_data.get('imagem'), 'forum')
            texto += u'<img src="%s" width="100%%" style="padding: 20px; margin: 0px !important;">' % filename
        try:
            conversa = Conversa.objects.filter(topico=topico, conversa_pai=None)[0]
            conversa.editor = editor
            conversa.texto = texto
        except:
            # Cria a Conversa com o texto informado
            conversa = Conversa(
                topico=topico,
                autor=editor,
                texto=texto,
            )
        conversa.save()
        if self.cleaned_data.get('arquivo'):
            conversa.arquivo.save(self.cleaned_data.get('arquivo').name, self.cleaned_data.get('arquivo'))
        return topico


class MoverTopicoForm(forms.ModelForm):
    class Meta:
        model = Topico
        fields = ('grupo',)


class ConversaForm(forms.ModelForm):
    class Meta:
        model = Conversa
        fields = ('texto', 'conversa_pai', 'arquivo', )
        widgets = {
            'texto': CKEditorWidget(config_name='basic'),
            'conversa_pai': forms.HiddenInput(),
        }

    imagem = forms.ImageField(label=u'Imagem', required=False)

    def save(self, topico, editor, *args, **kwargs):

        # se for a edição de uma conversa, não se pode atualizar o autor, apenas o editor
        if self.instance.pk:
            self.instance.editor = editor
            self.instance.editada = datetime.now()
        else:
            self.instance.autor = editor
            self.instance.topico = topico

        texto = self.cleaned_data.get('texto')
        if self.cleaned_data.get('imagem'):
            filename = save_file(self.cleaned_data.get('imagem'), 'forum')
            texto += u'<img src="%s" width="100%%" style="padding: 20px; margin: 0px !important;">' % filename
        self.instance.texto = texto
        return super(ConversaForm, self).save(*args, **kwargs)


class PesquisaForm(forms.Form):

    texto = forms.CharField(required=False)
    autor = forms.CharField(required=False)
    grupo = forms.CharField(required=False)
    listar_conversas = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput())

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


class AddMembrosForm(forms.Form):

    usuarios = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple, queryset=User.objects.all())

    def __init__(self, grupo, *args, **kwargs):
        super(AddMembrosForm, self).__init__(*args, **kwargs)
        self.grupo = grupo
        self.fields['usuarios'].queryset = User.objects.exclude(pk__in=grupo.grupousuario_set.values_list('usuario', flat=True)).exclude(is_active=False).order_by('first_name', 'username')

    def save(self, *args, **kwargs):
        for usuario in self.cleaned_data.get('usuarios'):
            GrupoUsuario.objects.get_or_create(grupo=self.grupo, usuario=usuario)


class AddPropostaForm(forms.ModelForm):
    class Meta:
        model = Proposta
        fields = ('texto', 'escopo', 'dt_encerramento' )
        widgets = {
            'texto': CKEditorWidget(config_name='basicadd'),
        }

    def save(self, topico, autor, *args, **kwargs):
        self.instance.topico = topico
        self.instance.autor = autor
        return super(AddPropostaForm, self).save(*args, **kwargs)


class AddEnqueteForm(forms.ModelForm):
    class Meta:
        model = Proposta
        fields = ('texto', 'escopo', 'dt_encerramento' )
        widgets = {
            'texto': CKEditorWidget(config_name='basicadd'),
        }

    def save(self, topico, autor, *args, **kwargs):
        self.instance.topico = topico
        self.instance.autor = autor
        return super(AddEnqueteForm, self).save(*args, **kwargs)


class VotoPropostaForm(forms.ModelForm):
    class Meta:
        model = Voto
        fields = ('voto', )

    justificativa = forms.CharField(label=u'Justificativa', widget=forms.Textarea, required=False)

    def save(self, proposta, eleitor, *args, **kwargs):
        self.instance.proposta = proposta
        self.instance.eleitor = eleitor

        if proposta.voto_set.filter(eleitor=eleitor).exists():
            for voto in proposta.voto_set.filter(eleitor=eleitor):
                voto.voto = self.cleaned_data.get('voto')

                if self.cleaned_data.get('justificativa'):
                    if voto.conversa:
                        voto.conversa.texto = self.cleaned_data.get('justificativa')
                        voto.conversa.save()
                    else:
                        conversa = Conversa(
                            topico=proposta.topico,
                            autor=eleitor,
                            texto=self.cleaned_data.get('justificativa'),
                            conversa_pai=proposta,
                        )
                        conversa.save()
                        voto.conversa = conversa
                voto.save()
            return
        else:
            if self.cleaned_data.get('justificativa'):
                conversa = Conversa(
                    topico=proposta.topico,
                    autor=eleitor,
                    texto=self.cleaned_data.get('justificativa'),
                    conversa_pai=proposta,
                )
                conversa.save()
                self.instance.conversa = conversa
        return super(VotoPropostaForm, self).save(*args, **kwargs)


class VotoEnqueteForm(forms.ModelForm):
    class Meta:
        model = Voto
        fields = ('opcao', )

    def __init__(self, proposta, *args, **kwargs):
        super(VotoEnqueteForm, self).__init__(*args, **kwargs)
        self.fields['opcao'].queryset = proposta.propostaopcao_set.all()

    def save(self, proposta, eleitor, *args, **kwargs):
        self.instance.proposta = proposta
        self.instance.eleitor = eleitor
        self.instance.voto = ''

        if proposta.voto_set.filter(eleitor=eleitor).exists():
            proposta.voto_set.filter(eleitor=eleitor).update(opcao=self.cleaned_data.get('opcao'))
            return
        return super(VotoEnqueteForm, self).save(*args, **kwargs)

