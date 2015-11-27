# -*- coding: utf-8 -*-
from django import forms
from django.contrib.localflavor.br.forms import BRCPFField, BRZipCodeField
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings

from municipios.models import UF

from captcha.fields import ReCaptchaField

from datetime import date
from models import Pessoa, Membro, Circulo
from cms.email import sendmail



class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = ('nome', 'email', 'uf', 'municipio', )

    captcha = ReCaptchaField()

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

    captcha = ReCaptchaField()

    def __init__(self, *args, **kwargs):
        super(MembroForm, self).__init__(*args, **kwargs)
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012, PSB 2001-2003)'
        self.fields['contrib_tipo'].choices = (('1', u'Mensal'), ('3', u'Trimestral'), ('6', u'Semestral'), ('A', u'Anual'), ('O', u'Não pretende fazer'), )
        self.fields['contrib_tipo'].help_text = u'Tanto o tipo de contribuição como o valor podem ser alterados a qualquer momento aqui no site. Basta solicitar a alteração no cadastro'

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
        fields = ('fundador', 'nome', 'email', 'cpf', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento', 'nome_da_mae', 'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral',
            'zona_eleitoral', 'secao_eleitoral', 'filiacao_partidaria', 'contrib_tipo', 'contrib_valor', 'estadocivil',
            'endereco', 'endereco_num', 'endereco_complemento', 'endereco_cep', )

    cpf = BRCPFField(
        label='CPF',
        error_messages={
            'invalid':u'Preencha corretamente o seu CPF.',
            'max_digits': u'Certifique-se de que o valor tenha no máximo 11 números no formato: XXX.XXX.XXX-XX.',
            'digits_only': u'Preencha apenas com números, ou no formato: XXX.XXX.XXX-XX.',
        }
    )
    endereco_cep = BRZipCodeField(label=u'CEP', required=False)
    captcha = ReCaptchaField()

    def __init__(self, *args, **kwargs):
        super(FiliadoForm, self).__init__(*args, **kwargs)
        self.fields['nome_da_mae'].required = True
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012)'
        self.fields['contrib_tipo'].choices = (('1', u'Mensal'), ('3', u'Trimestral'), ('6', u'Semestral'), ('A', u'Anual'), ('O', u'Não pretende fazer'), )
        self.fields['contrib_tipo'].help_text = u'Tanto o tipo de contribuição como o valor podem ser alterados a qualquer momento aqui no site. Basta solicitar a alteração no cadastro'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email.')
        return email

    def clean_estadocivil(self):
        estadocivil = self.cleaned_data.get('estadocivil')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not estadocivil:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return estadocivil

    def clean_atividade_profissional(self):
        atividade_profissional = self.cleaned_data.get('atividade_profissional')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not atividade_profissional:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return atividade_profissional

    def clean_uf_eleitoral(self):
        uf_eleitoral = self.cleaned_data.get('uf_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not uf_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return uf_eleitoral

    def clean_municipio_eleitoral(self):
        municipio_eleitoral = self.cleaned_data.get('municipio_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not municipio_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return municipio_eleitoral

    def clean_titulo_eleitoral(self):
        titulo_eleitoral = self.cleaned_data.get('titulo_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not titulo_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return titulo_eleitoral

    def clean_zona_eleitoral(self):
        zona_eleitoral = self.cleaned_data.get('zona_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not zona_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return zona_eleitoral

    def clean_secao_eleitoral(self):
        secao_eleitoral = self.cleaned_data.get('secao_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not secao_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return secao_eleitoral

    def clean_endereco_cep(self):
        endereco_cep = self.cleaned_data.get('endereco_cep')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not endereco_cep:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return endereco_cep

    def clean_endereco(self):
        endereco = self.cleaned_data.get('endereco')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not endereco:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return endereco

    def clean_endereco_num(self):
        endereco_num = self.cleaned_data.get('endereco_num')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not endereco_num:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return endereco_num

    def clean_municipio(self):
        municipio = self.cleaned_data.get('municipio')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not municipio:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return municipio

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf and Membro.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse cpf.')
        return cpf

    def save(self, commit=True):
        self.instance.filiado = True
        return super(FiliadoForm, self).save(commit)


class AtualizarCadastroLinkForm(forms.Form):
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

    def clean(self):
        cleaned_data = super(AtualizarCadastroLinkForm, self).clean()
        email = cleaned_data.get('email')
        cpf = cleaned_data.get('cpf')

        if not email and not cpf:
            raise forms.ValidationError(u'É preciso informar um e-mail ou um CPF.')

        if (not email or not Membro.objects.filter(email=email).exists()) and (not cpf or not Membro.objects.filter(cpf=cpf).exists()):
            raise forms.ValidationError(u'Não existe nenhum cadastro com esse e-mail ou CPF.')
        return cleaned_data

    def sendmail(self, template_email_name):
        try:
            membro = Membro.objects.get(email=self.cleaned_data['email'])
        except Membro.DoesNotExist:
            membro = Membro.objects.get(cpf=self.cleaned_data['cpf'])
        sendmail(
            subject=u'Atualização de Cadastro do Raíz.',
            to=[membro.email, ],
            template=template_email_name,
            params={
                'membro': membro,
                'link': u'%s%s' % (settings.SITE_HOST, membro.get_absolute_update_url()),
            },
        )


class AtualizarCadastroFiliadoForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('fundador', 'nome', 'email', 'cpf', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento', 'nome_da_mae', 'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral',
            'zona_eleitoral', 'secao_eleitoral', 'filiacao_partidaria', 'contrib_tipo', 'contrib_valor', 'estadocivil',
            'endereco', 'endereco_num', 'endereco_complemento', 'endereco_cep', )

    cpf = BRCPFField(
        label='CPF',
        error_messages={
            'invalid':u'Preencha corretamente o seu CPF.',
            'max_digits': u'Certifique-se de que o valor tenha no máximo 11 números no formato: XXX.XXX.XXX-XX.',
            'digits_only': u'Preencha apenas com números, ou no formato: XXX.XXX.XXX-XX.',
        }
    )
    endereco_cep = BRZipCodeField(label=u'CEP', required=False)

    def __init__(self, *args, **kwargs):
        super(AtualizarCadastroFiliadoForm, self).__init__(*args, **kwargs)
        self.fields['nome_da_mae'].required = True
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012)'
        self.fields['contrib_tipo'].choices = (('1', u'Mensal'), ('3', u'Trimestral'), ('6', u'Semestral'), ('A', u'Anual'), ('O', u'Não pretende fazer'), )
        self.fields['contrib_tipo'].help_text = u'Tanto o tipo de contribuição como o valor podem ser alterados a qualquer momento aqui no site. Basta solicitar a alteração no cadastro'

    def clean_estadocivil(self):
        estadocivil = self.cleaned_data.get('estadocivil')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not estadocivil:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return estadocivil

    def clean_atividade_profissional(self):
        atividade_profissional = self.cleaned_data.get('atividade_profissional')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not atividade_profissional:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return atividade_profissional

    def clean_uf_eleitoral(self):
        uf_eleitoral = self.cleaned_data.get('uf_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not uf_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return uf_eleitoral

    def clean_municipio_eleitoral(self):
        municipio_eleitoral = self.cleaned_data.get('municipio_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not municipio_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return municipio_eleitoral

    def clean_titulo_eleitoral(self):
        titulo_eleitoral = self.cleaned_data.get('titulo_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not titulo_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return titulo_eleitoral

    def clean_zona_eleitoral(self):
        zona_eleitoral = self.cleaned_data.get('zona_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not zona_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return zona_eleitoral

    def clean_secao_eleitoral(self):
        secao_eleitoral = self.cleaned_data.get('secao_eleitoral')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not secao_eleitoral:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return secao_eleitoral

    def clean_endereco_cep(self):
        endereco_cep = self.cleaned_data.get('endereco_cep')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not endereco_cep:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return endereco_cep

    def clean_endereco(self):
        endereco = self.cleaned_data.get('endereco')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not endereco:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return endereco

    def clean_endereco_num(self):
        endereco_num = self.cleaned_data.get('endereco_num')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not endereco_num:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return endereco_num

    def clean_municipio(self):
        municipio = self.cleaned_data.get('municipio')
        fundador = self.cleaned_data.get('fundador')
        if fundador and not municipio:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')
        return municipio

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email.')
        return email

    def save(self, commit=True):
        self.instance.filiado = True
        self.instance.status_email = 'A'
        return super(AtualizarCadastroFiliadoForm, self).save(commit)


class AtualizarCadastroMembroForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('nome', 'email', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'filiacao_partidaria', 'contrib_tipo', 'contrib_valor')

    def __init__(self, *args, **kwargs):
        super(AtualizarCadastroMembroForm, self).__init__(*args, **kwargs)
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012, PSB 2001-2003)'
        self.fields['contrib_tipo'].choices = (('1', u'Mensal'), ('3', u'Trimestral'), ('6', u'Semestral'), ('A', u'Anual'), ('O', u'Não pretende fazer'), )
        self.fields['contrib_tipo'].help_text = u'Tanto o tipo de contribuição como o valor podem ser alterados a qualquer momento aqui no site. Basta solicitar a alteração no cadastro'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email.')
        return email

    def save(self, commit=True):
        self.instance.status_email = 'A'
        return super(AtualizarCadastroMembroForm, self).save(commit)


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
    circulo = forms.ModelChoiceField(label=u'Círculo', required=False, queryset=Circulo.objects.all())
