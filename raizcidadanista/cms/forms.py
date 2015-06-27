# coding: utf-8
from django import forms
from django.db.models import Q
from django.conf import settings
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.utils.html import mark_safe
from django.core.urlresolvers import reverse
from datetime import datetime, date

from captcha.fields import CaptchaField
from ckeditor.widgets import CKEditorWidget

from models import SectionItem, ArticleComment, Recurso, Theme, Article, \
    GroupType, EmailAgendado
from cms.email import sendmail

import os, zipfile


class SectionItemCustomForm(forms.ModelForm):
    created_at = forms.DateTimeField(required=False)

    class Meta:
        model = SectionItem

class ArticleCommentForm(forms.ModelForm):
    class Meta:
        model = ArticleComment
        exclude = ('article', )

    email = forms.EmailField()

    def _create_messagem(self):
        menssagem = u'''
            <h1>Novo comentário no artigo %(article)s</h1>
            <b>Nome:</b> %(author)s<br>
            <b>Email:</b> %(email)s<br>
            <b>Mensagem:</b> %(comment)s<br>
        ''' % {
                'article': self.instance.article,
                'author': self.cleaned_data['author'],
                'email': self.cleaned_data['email'],
                'comment': self.cleaned_data['comment'],
            }
        return menssagem

    def sendemail(self):
        EMAILADMIN = Recurso.objects.get_or_create(recurso=u'EMAILADMIN')[0]
        if EMAILADMIN.valor:
            menssagem = self._create_messagem()
            menssagem += u'<a href="%s%s">Acessar</a>' % (settings.SITE_HOST, reverse('admin:cms_article_change', args=(self.instance.article.pk, )))
            sendmail(
                subject=u'%s - Novo comentário' % Recurso.objects.get(recurso='SITE_NAME').valor,
                to=EMAILADMIN.valor.split('\n'),
                template=menssagem,
                headers={'Reply-To': self.cleaned_data['email']}
            )


class ThemeForm(forms.ModelForm):
    class Meta:
        model = Theme

    theme = forms.FileField(
        label=u'Template',
        help_text=mark_safe(u'''Arquivo .zip com a seguinte estrutura:<br>
            PASTA<br>
            &nbsp&nbsp&nbsp&nbsptemplatetags/<br>
            &nbsp&nbsp&nbsp&nbsptemplates/<br>
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsphome.html<br>
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsparticle.html<br>
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspsession.html<br>
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspsearch.html<br>
            &nbsp&nbsp&nbsp&nbspstatic/<br>
            &nbsp&nbsp&nbsp&nbspviews.py<br>
            &nbsp&nbsp&nbsp&nbspurl.py<br>
            &nbsp&nbsp&nbsp&nbsp__init__.py''')
    )

    def _path_nome(self, zip):
        first_dir = zip.namelist()[0]
        return first_dir

    def have_first_dir(self, zip):
        first_dir = zip.namelist()[0]
        for filename in zip.namelist():
            if not first_dir in filename:
                return False
        return True

    def clean_theme(self):
        theme = self.cleaned_data.get('theme')
        if theme.name.split('.')[-1].lower() != 'zip':
            raise forms.ValidationError(u'Envie um arquivo .zip. Siga as instruções abaixo.')
        
        try:
            zip = zipfile.ZipFile(theme, 'r')
        except:
            raise forms.ValidationError(u'O arquivo .zip está corrompido.')
        
        if not self.have_first_dir(zip):
            raise forms.ValidationError(u'O template enviado não possui uma pasta inicial.')
        return theme

    def save(self, commit=True):
        theme = self.cleaned_data.get('theme')
        zip = zipfile.ZipFile(theme, 'r')

        # Cria diretório do theme
        dirname = os.path.join(settings.MEDIA_ROOT, 'uploads', 'themes')
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        # Extrai o zip do template
        with zipfile.ZipFile(self.cleaned_data.get('theme'), "r") as z:
            z.extractall(dirname)
        self.instance.path = os.path.join(dirname, self._path_nome(zip))
        self.instance.path_name = self._path_nome(zip)
        return super(ThemeForm, self).save(commit)


class CustomGroupForm(forms.ModelForm):
    class Meta:
        model = Group

    def __init__(self, *args, **kwargs):
        super(CustomGroupForm, self).__init__(*args, **kwargs)
        choices = []
        for query in self.fields['permissions'].queryset:
            name = query.name
            if u"Can add" in name: name = name.replace(u"Can add", u"Pode adicionar")
            if u"Can change" in name: name = name.replace(u"Can change", u"Pode editar")
            if u"Can delete" in name: name = name.replace(u"Can delete", u"Pode remover")
            choices.append((query.pk, name))
        self.fields['permissions'].widget.choices = choices


class PowerArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('title', 'slug', 'content', 'sections',)
        widgets = {
            'content': CKEditorWidget(),
            'sections': FilteredSelectMultiple(u"Seções", False, attrs={'rows':'10'}),
        }


class UpdateForm(forms.Form):

    version = forms.CharField(label=u'Versão', required=False, help_text=u'Deixe em branco para atualizar para a ultima versão.')

    def clean_version(self):
        version = self.cleaned_data.get('version')
        if version:
            if float(settings.VERSION.replace('v', '')) > float(version.replace('v', '')):
                raise forms.ValidationError(u'Não é possível atualizar para uma versão inferior a %s' % settings.VERSION)
        return version


class CMSUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(u'Esse email já está cadastrado.')
        return email

    def __init__(self, *args, **kwargs):
        super(CMSUserCreationForm, self).__init__(*args, **kwargs)
        for grouptype in GroupType.objects.all():
            self.fields['grouptype_%s' % grouptype.pk] = forms.ModelChoiceField(label=grouptype.name, queryset=grouptype.groupitem_set.all())

    def save(self, commit=True):
        super(CMSUserCreationForm, self).save(commit)
        
        self.instance.is_staff = False
        self.instance.is_active = False
        if Group.objects.filter(name=u'Pendente').exists():
            self.instance.groups.add(Group.objects.get(name=u'Pendente'))

        for grouptype in GroupType.objects.all():
            self.instance.groups.add(self.cleaned_data['grouptype_%s' % grouptype.pk].group)
        self.instance.save()

        today = date.today()
        if not EmailAgendado.objects.filter(subject=u'Novo usuário solicitou o registro no site', date__year=today.year, date__month=today.month, date__day=today.day).exists():
            menssagem = u'Novo usuário solicitou o registro no site. Clique <a href="%s%s?is_active__exact=0">aqui</a> para visualizar.' % (settings.SITE_HOST, reverse('admin:auth_user_changelist'))
            sendmail(
                subject=u'Novo usuário solicitou o registro no site',
                to=Recurso.objects.get_or_create(recurso=u'EMAILADMIN')[0].valor.split('\n'),
                template=menssagem
            )