# -*- coding: utf-8 -*-
from django import forms
from django.contrib.localflavor.br.forms import BRCPFField, BRZipCodeField
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.core.validators import URLValidator
from django.conf import settings

from municipios.models import UF

from ckeditor.widgets import CKEditorWidget
from captcha.fields import ReCaptchaField

from datetime import date
from models import Pessoa, Membro, CirculoMembro, Circulo, Campanha, Lista, ArticleCadastro, \
    CirculoPendente, CIRCULO_PENDENTE_TIPO, CIRCULO_PENDENTE_STATUS
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
        fields = ('nome', 'apelido', 'email', 'cpf', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'filiacao_partidaria', 'contrib_tipo', 'contrib_valor')

    cpf = BRCPFField(
        label='CPF',
        error_messages={
            'invalid':u'Preencha corretamente o seu CPF.',
            'max_digits': u'Certifique-se de que o valor tenha no máximo 11 números no formato: XXX.XXX.XXX-XX.',
            'digits_only': u'Preencha apenas com números, ou no formato: XXX.XXX.XXX-XX.',
        }
    )

    def __init__(self, *args, **kwargs):
        super(MembroForm, self).__init__(*args, **kwargs)
        for field in ('email', 'municipio', ):
            self.fields[field].required = True
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012, PSB 2001-2003)'
        self.fields['contrib_tipo'].choices = (('1', u'Mensal'), ('3', u'Trimestral'), ('6', u'Semestral'), ('A', u'Anual'), ('O', u'Não pretende fazer'), )
        self.fields['contrib_tipo'].help_text = u'Tanto o tipo de contribuição como o valor podem ser alterados a qualquer momento aqui no site. Basta solicitar a alteração no cadastro'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email. Faça login no site para que possa alterar seus dados.')
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf and Membro.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse CPF.')
        return cpf

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
                    change_message = u'Nome alterado de %s para %s pelo formulário' % (pessoa.nome, self.instance.nome)
                )

        return super(MembroForm, self).save(commit)


class FiliadoForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ('fundador', 'nome', 'apelido', 'email', 'cpf', 'rg', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento', 'nome_da_mae', 'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral',
            'zona_eleitoral', 'secao_eleitoral', 'filiacao_partidaria', 'contrib_tipo', 'contrib_valor', 'estadocivil', 'uf_naturalidade', 'municipio_naturalidade',
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
        super(FiliadoForm, self).__init__(*args, **kwargs)
        # Requireds
        for field in ('email', 'municipio', 'nome_da_mae', 'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral', 'zona_eleitoral', 'secao_eleitoral', ):
            self.fields[field].required = True
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012)'
        self.fields['contrib_tipo'].choices = (('1', u'Mensal'), ('3', u'Trimestral'), ('6', u'Semestral'), ('A', u'Anual'), )
        self.fields['contrib_tipo'].help_text = u'Tanto o tipo de contribuição como o valor podem ser alterados a qualquer momento aqui no site. Basta solicitar a alteração no cadastro'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Membro.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse email.')
        return email

    def testa_fundador(self, campo):
        fundador = self.cleaned_data.get('fundador')
        if fundador and not campo:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')

    def clean_estadocivil(self):
        campo = self.cleaned_data.get('estadocivil')
        self.testa_fundador(campo)
        return campo

    def clean_atividade_profissional(self):
        campo = self.cleaned_data.get('atividade_profissional')
        self.testa_fundador(campo)
        return campo

    def clean_endereco_cep(self):
        campo = self.cleaned_data.get('endereco_cep')
        self.testa_fundador(campo)
        return campo

    def clean_endereco(self):
        campo = self.cleaned_data.get('endereco')
        self.testa_fundador(campo)
        return campo

    def clean_endereco_num(self):
        campo = self.cleaned_data.get('endereco_num')
        self.testa_fundador(campo)
        return campo

    def clean_municipio(self):
        campo = self.cleaned_data.get('municipio')
        self.testa_fundador(campo)
        return campo

    def clean_uf_naturalidade(self):
        campo = self.cleaned_data.get('uf_naturalidade')
        self.testa_fundador(campo)
        return campo

    def clean_municipio_naturalidade(self):
        campo = self.cleaned_data.get('municipio_naturalidade')
        self.testa_fundador(campo)
        return campo

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf and Membro.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError(u'Já existe um cadastro com esse CPF.')
        return cpf

    def save(self, commit=True):
        email = self.cleaned_data.get('email')
        self.instance.filiado = True

        # Converte Pessoa em Filiado
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
                    change_message = u'Nome alterado de %s para %s pelo formulário' % (pessoa.nome, self.instance.nome)
                )
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

        if not membro.status_email in ('S', 'O'):
            sendmail(
                subject=u'Atualização de Cadastro.',
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
        fields = ('fundador', 'nome', 'apelido', 'email', 'cpf', 'rg', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'dtnascimento', 'nome_da_mae', 'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral',
            'zona_eleitoral', 'secao_eleitoral', 'filiacao_partidaria', 'contrib_tipo', 'contrib_valor', 'estadocivil', 'uf_naturalidade', 'municipio_naturalidade',
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
        # Requireds
        for field in ('email', 'municipio', 'nome_da_mae', 'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral', 'zona_eleitoral', 'secao_eleitoral', ):
            self.fields[field].required = True
        self.fields['filiacao_partidaria'].label = 'Filiação Partidária (Exemplo PT 1989-2004, PSOL 2005-2012)'
        self.fields['contrib_tipo'].choices = (('1', u'Mensal'), ('3', u'Trimestral'), ('6', u'Semestral'), ('A', u'Anual'), )
        self.fields['contrib_tipo'].help_text = u'Tanto o tipo de contribuição como o valor podem ser alterados a qualquer momento aqui no site. Basta solicitar a alteração no cadastro'

    def testa_fundador(self, campo):
        fundador = self.cleaned_data.get('fundador')
        if fundador and not campo:
            raise forms.ValidationError(u'Este campo é obrigatório se você marcou "Quero assinar a ata de fundação da RAiZ".')

    def clean_estadocivil(self):
        campo = self.cleaned_data.get('estadocivil')
        self.testa_fundador(campo)
        return campo

    def clean_atividade_profissional(self):
        campo = self.cleaned_data.get('atividade_profissional')
        self.testa_fundador(campo)
        return campo

    def clean_endereco_cep(self):
        campo = self.cleaned_data.get('endereco_cep')
        self.testa_fundador(campo)
        return campo

    def clean_endereco(self):
        campo = self.cleaned_data.get('endereco')
        self.testa_fundador(campo)
        return campo

    def clean_endereco_num(self):
        campo = self.cleaned_data.get('endereco_num')
        self.testa_fundador(campo)
        return campo

    def clean_municipio(self):
        campo = self.cleaned_data.get('municipio')
        self.testa_fundador(campo)
        return campo

    def clean_uf_naturalidade(self):
        campo = self.cleaned_data.get('uf_naturalidade')
        self.testa_fundador(campo)
        return campo

    def clean_municipio_naturalidade(self):
        campo = self.cleaned_data.get('municipio_naturalidade')
        self.testa_fundador(campo)
        return campo

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
        fields = ('nome', 'apelido', 'email', 'cpf', 'rg', 'uf', 'municipio', 'sexo', 'celular', 'residencial',
            'atividade_profissional', 'filiacao_partidaria', 'contrib_tipo', 'contrib_valor')

    cpf = BRCPFField(
        label='CPF',
        error_messages={
            'invalid':u'Preencha corretamente o seu CPF.',
            'max_digits': u'Certifique-se de que o valor tenha no máximo 11 números no formato: XXX.XXX.XXX-XX.',
            'digits_only': u'Preencha apenas com números, ou no formato: XXX.XXX.XXX-XX.',
        }
    )

    def __init__(self, *args, **kwargs):
        super(AtualizarCadastroMembroForm, self).__init__(*args, **kwargs)
        for field in ('email', 'municipio', ):
            self.fields[field].required = True
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

class ConsultaForm(forms.Form):
    nome = forms.CharField(label='Nome ou email')

    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        if not '@' in nome and len(nome.split(' ')) < 2:
            raise forms.ValidationError(u'Informe o nome e sobrenome ou o email.')
        return nome


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
    grupo = forms.ModelChoiceField(label=u'Grupo', required=False, queryset=Group.objects.all())
    tipo = forms.ChoiceField(label=u'Tipo de pessoa', required=False, choices=TIPO_CHOICES)
    uf = forms.ModelChoiceField(label=u'UF', required=False, queryset=UF.objects.all())
    circulo = forms.ModelChoiceField(label=u'Círculo', required=False, queryset=Circulo.objects.all())



class ArticleCadastroForm(forms.ModelForm):
    class Meta:
        model = ArticleCadastro
        widgets = {
            'header': CKEditorWidget(),
            'content': CKEditorWidget(),
        }
    link = forms.BooleanField(label=u'Cadastro de link?', required=False)
    upload = forms.ImageField(label=u"Imagem", required=False)

    def clean_title(self):
        title = self.cleaned_data.get('title')
        link = self.cleaned_data.get('link')
        if not link and not title:
            raise forms.ValidationError(u'Este campo é obrigatório.')
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content')
        link = self.cleaned_data.get('link')
        if link:
            URLValidator()(content)
        return content

    def __init__(self, *args, **kwargs):
        super(ArticleCadastroForm, self).__init__(*args, **kwargs)
        self.fields['title'].required = False

        if self.instance and str(self.instance.pk) == self.instance.slug:
            self.fields['link'].initial = True


class InclusaoEmLoteForm(forms.Form):
    arquivo = forms.FileField(help_text=u'Arquivo .csv onde cada linha está no formato: email, nome da pessoa, telefone, uf, número do círculo (opcional)')

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']
        if arquivo.name.split('.')[-1].lower() != 'csv':
            raise forms.ValidationError(u'Envie um arquivo .csv.')
        return arquivo


class ImportarPessoasListaForm(forms.Form):
    lista = forms.ModelChoiceField(queryset=Lista.objects.all())
    arquivo = forms.FileField(help_text=u'Arquivo .csv onde cada linha contém um email')

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']
        if arquivo.name.split('.')[-1].lower() != 'csv':
            raise forms.ValidationError(u'Envie um arquivo .csv.')
        return arquivo


class CirculoPendenteForm(forms.ModelForm):
    class Meta:
        model = CirculoPendente
        fields = ('primeiravez', 'circulo', 'atualizar', 'titulo', 'dtcriacao', 'tipo', 'uf', 'municipio', 'area_geografica', 'status', 'num_membros', 'num_membros_coleta', 'jardineiro_1_nome', 'jardineiro_1_email', 'jardineiro_1_telefone', 'jardineiro_2_nome', 'jardineiro_2_email', 'jardineiro_2_telefone', 'site_externo', 'ferramentas', 'reunioes', 'atividades', 'descricao', )

    PRIMEIRAVEZ_CHOICES = (
        ('T', u'Sim, pela primeira vez'),
        ('F', u'Não, agora estou atualizando ou corrigindo'),
    )
    primeiravez = forms.ChoiceField(label=u'Preenchendo este Formulário pela 1ª vez?', choices=PRIMEIRAVEZ_CHOICES, initial='T', widget=forms.RadioSelect())
    atualizar = forms.ModelChoiceField(label=u'Selecione o Círculo que deseja editar', queryset=CirculoPendente.objects.all(), required=False)

    tipo = forms.ChoiceField(label=u'Tipo de Círculo', choices=CIRCULO_PENDENTE_TIPO, initial='R', widget=forms.RadioSelect())
    status = forms.ChoiceField(label=u'Este Círculo está em atividade atualmente ?', choices=CIRCULO_PENDENTE_STATUS, widget=forms.RadioSelect())

    def __init__(self, request, *args, **kwargs):
        super(CirculoPendenteForm, self).__init__(*args, **kwargs)
        self.instance.autor = request.user
        self.fields['atualizar'].queryset = CirculoPendente.objects.filter(autor=request.user)
        self.fields['circulo'].queryset = Circulo.objects.filter(circulomembro__administrador=True, circulomembro__membro__usuario=request.user)

    def clean_atualizar(self):
        atualizar = self.cleaned_data.get('atualizar')
        if not atualizar and self.cleaned_data.get('primeiravez') ==  'F':
            raise forms.ValidationError(u'Este campo é obrigatório.')
        return atualizar

    def sendmail(self, template_email_name='emails/cadastro-circulo.html'):
        sendmail(
            subject=u'Criação/Atualização de Círculo',
            to=['correio@raiz.org.br', ],
            template=template_email_name,
            params={
                'circulo': self.instance,
                'SITE_HOST': settings.SITE_HOST,
            },
        )