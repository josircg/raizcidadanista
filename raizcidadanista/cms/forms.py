# coding: utf-8
from django import forms
from django.db.models import Q
from django.conf import settings
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.template import loader
from django.utils.http import int_to_base36
from django.contrib.sites.models import get_current_site
from django.utils.html import mark_safe
from django.core.urlresolvers import reverse
from datetime import datetime, date

from captcha.fields import ReCaptchaField
from ckeditor.widgets import CKEditorWidget

from models import SectionItem, ArticleComment, Recurso, Article, \
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
        exclude = ('article', 'active', )

    email = forms.EmailField()
    captcha = ReCaptchaField()

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
            if u"Can view" in name: name = name.replace(u"Can view", u"Pode visualizar")
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


class CustomPasswordResetForm(PasswordResetForm):
    def save(self, domain_override=None,
        subject_template_name='registration/password_reset_subject.txt',
        email_template_name='registration/password_reset_email.html',
        use_https=False, token_generator=default_token_generator,
        from_email=None, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        for user in self.users_cache[:1]:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            sendmail(
                subject=subject,
                to=[user.email],
                params=c,
                template=email_template_name,
            )


class ContatoForm(forms.Form):
    nome = forms.CharField(u'Nome', required=True)
    email = forms.EmailField(u'Email', required=True)
    mensagem = forms.CharField(u'Mensagem', widget=forms.Textarea(), required=True)
    captcha = ReCaptchaField()

    def sendemail(self):
        nome = self.cleaned_data.get('nome')
        email = self.cleaned_data.get('email')
        mensagem = self.cleaned_data.get('mensagem')
        sendmail(
            subject = u'Raiz Cidadanista - Formulário de contato',
            to = ['correio@raiz.org.br', ],
            params = {
                'nome': nome,
                'email': email,
                'mensagem': mensagem,
            },
            template = 'emails/contato.html',
            headers = {
                'Reply-To': email,
            }
        )
