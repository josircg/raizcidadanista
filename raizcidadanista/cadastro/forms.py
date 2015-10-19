# -*- coding: utf-8 -*-
from django import forms
from django.contrib.localflavor.br.forms import BRCPFField
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings

from django.utils.http import int_to_base36
from django.utils.crypto import salted_hmac

from municipios.models import UF

from models import Pessoa, Membro
from cms.email import sendmail



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
            'atividade_profissional', 'filiacao_partidaria', 'contrib_tipo', 'contrib_valor')

    def __init__(self, *args, **kwargs):
        super(MembroForm, self).__init__(*args, **kwargs)
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012, PSB 2001-2003)'
        self.fields['contrib_tipo'].choices = (('1', u'Mensal'), ('3', u'Trimestral'), ('6', u'Semestral'), ('A', u'Anual'), ('O', u'Não pretende fazer'), )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email. Faça login no site para que possa alterar seus dados.')
        return email

    def save(self, commit=True):
        email = self.cleaned_data.get('email')

        # Converte Pessoa em Membro
        if Pessoa.objects.filter(email=email).exists():
            pessoa = Pessoa.objects.get(email=email)
            self.instance.pessoa_ptr = pessoa
            self.instance.status_email = pessoa.status_email

            if self.instance.nome != pessoa.nome:
                user = User.objects.get_or_create(username="sys")[0]
                LogEntry.objects.log_action(
                    user_id = user.pk,
                    content_type_id = ContentType.objects.get_for_model(pessoa).pk,
                    object_id = pessoa.pk,
                    object_repr = u"%s" % pessoa,
                    action_flag = CHANGE,
                    change_message = u'Nome alterado de %s para %s pelo cadastro de Membro.' % (pessoa.nome, self.instance.nome)
                )

        return super(MembroForm, self).save(commit)


class FiliadoForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('nome', 'email', 'cpf', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento', 'nome_da_mae',
            'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral', 'zona_eleitoral', 'secao_eleitoral', 'filiacao_partidaria',
             'contrib_tipo', 'contrib_valor', )

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
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012)'
        self.fields['contrib_tipo'].choices = (('1', u'Mensal'), ('3', u'Trimestral'), ('6', u'Semestral'), ('A', u'Anual'), ('O', u'Não pretende fazer'), )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email.')
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf and Membro.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse cpf.')
        return cpf

    def save(self, commit=True):
        self.instance.filiado = True
        return super(FiliadoForm, self).save(commit)


class FiliadoAtualizarLinkForm(forms.Form):
    email = forms.EmailField(label=u'e-mail', required=False)
    cpf = BRCPFField(
        label='CPF',
        required=False,
        error_messages={
            'invalid':u'Preencha corretamente o seu CPF.',
            'max_digits': u'Certifique-se de que o valor tenha no máximo 11 números no formato: XXX.XXX.XXX-XX.',
            'digits_only': u'Preencha apenas com números, ou no formato: XXX.XXX.XXX-XX.',
        }
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Não existe nenhum cadastro com esse email.')
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf and not Membro.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError(u'Não existe nenhum cadastro com esse CPF.')
        return cpf

    def clean(self):
        cleaned_data = super(FiliadoAtualizarLinkForm, self).clean()
        if not cleaned_data.get('email') and not cleaned_data.get('cpf'):
            raise forms.ValidationError(u'É preciso informar um e-mail ou um CPF.')
        return cleaned_data

    def sendmail(self, template_email_name):

        def create_token(filiado):
            key_salt = "cadastro.forms.FiliadoAtualizarLinkForm"
            value = u'%s%s' % (filiado.pk, filiado.email)
            return salted_hmac(key_salt, value).hexdigest()[::2]

        if self.cleaned_data.get('email'):
            filiado = Membro.objects.get(email=self.cleaned_data['email'])
        if self.cleaned_data.get('cpf'):
            filiado = Membro.objects.get(cpf=self.cleaned_data['cpf'])
        sendmail(
            subject=u'Atualização de Cadastro do Raíz.',
            to=[filiado.email, ],
            template=template_email_name,
            params={
                'filiado': filiado,
                'link': u'%s%s' % (settings.SITE_HOST, reverse('filiado_atualizar', kwargs={'uidb36': int_to_base36(filiado.pk), 'token': create_token(filiado)})),
            },
        )


class FiliadoAtualizarForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('nome', 'email', 'cpf', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento', 'nome_da_mae',
            'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral', 'zona_eleitoral', 'secao_eleitoral', 'filiacao_partidaria',)

    cpf = BRCPFField(
        label='CPF',
        error_messages={
            'invalid':u'Preencha corretamente o seu CPF.',
            'max_digits': u'Certifique-se de que o valor tenha no máximo 11 números no formato: XXX.XXX.XXX-XX.',
            'digits_only': u'Preencha apenas com números, ou no formato: XXX.XXX.XXX-XX.',
        }
    )

    def __init__(self, *args, **kwargs):
        super(FiliadoAtualizarForm, self).__init__(*args, **kwargs)
        self.fields['nome_da_mae'].required = True
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012)'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email.')
        return email

    def save(self, commit=True):
        self.instance.filiado = True
        return super(FiliadoAtualizarForm, self).save(commit)


class MembroImport(forms.Form):
    arquivo = forms.FileField()

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']
        if arquivo.name.split('.')[-1].lower() != 'csv':
            raise forms.ValidationError(u'Envie um arquivo .csv.')
        return arquivo


class MalaDiretaForm(forms.Form):
    TIPO_CHOICES = (
        ('', u'--------'),
        ('V', u'Visitante'),
        ('C', u'Colaborador'),
        ('F', u'Filiado'),
    )
    tipo = forms.ChoiceField(label=u'Tipo de pessoa', required=False, choices=TIPO_CHOICES)
    uf = forms.ModelChoiceField(label=u'UF', required=False, queryset=UF.objects.all())