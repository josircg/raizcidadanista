# coding: utf-8
from django.core.urlresolvers import reverse
from django.db.models import signals
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.contrib.auth.models import Group, User

from mptt.models import MPTTModel, TreeForeignKey
from smart_selects.db_fields import ChainedForeignKey
from uuidfield import UUIDField
from easy_thumbnails.files import get_thumbnailer

from signals import slug_pre_save
from fields import ListField
from datetime import datetime
from email import sendmail, resendmail_email_agendado

import os, shutil, re


class ItemManager(models.Manager):

    use_for_related_fields = True

    def active(self):
        return self.get_query_set().filter(is_active=True)

ARTICLE_COMMENTS_CHOICES = (
    ('A', u'Permite comentários'),
    ('P', u'Permite comentários privados'),
    ('F', u'Fechado para novos comentários'),
    ('N', u'Sem comentários'),
)
class Article(models.Model):
    title = models.CharField(u'Título', max_length=250)
    slug = models.SlugField(u'slug', max_length=250, unique=True, db_index=True, blank=True)
    header = models.TextField(u'Chamada', null=True, blank=True, default=None) # HTML que aparecerá na página principal caso o artigo esteja na home
    content = models.TextField(u'Conteúdo', null=True, blank=True, default=None)  # HTML
    author = models.ForeignKey('auth.User', verbose_name=u'Autor')
    keywords = models.TextField(u'Palavras Chaves', null=True, blank=True, default=None) # é utilizada como Keyword para ranking Google
    created_at = models.DateField(u'Dt.Criação', default=timezone.now)
    updated_at = models.DateField(u'Dt.Alteração', auto_now=True)
    is_active = models.BooleanField(u'Está ativo?', default=True)
    allow_comments = models.CharField(u'Comentários', max_length=1, choices=ARTICLE_COMMENTS_CHOICES, default='N')
    views = models.IntegerField(u'Visualizações', default=0)
    conversions = models.IntegerField(u'Conversões', default=0)

    sections = models.ManyToManyField('Section', through='SectionItem', null=True, blank=True)
    slug_conf = {'field': 'slug', 'from': 'title'}

    objects = ItemManager()

    def __unicode__(self):
        return u'%s' % (self.title, )

    class Meta:
        verbose_name = u'Artigo'
        ordering = ['-created_at', ]
        permissions = (
            ("manage_articles", u"Administrar artigos"),
        )


    def get_absolute_url(self):
        return reverse('article', kwargs={'slug': self.slug})

    def get_conversion_url(self):
        link = reverse('link', kwargs={'article_slug': self.slug})
        return u'%s%s?next=' % (settings.SITE_HOST, link, )
    get_conversion_url.short_description = u'URL de conversão'

    def have_perm(self, user):
        if user.is_superuser or not self.sections.count():
            return True
        for section in self.sections.all():
            if not section.permissao_set.count():
                return True
            if not user.groups.filter(pk__in=section.permissao_set.values_list('pk', flat=True)).exists():
                return False
        return True

    def get_images(self):
        rex = re.compile(r'(<img )(.*)(src=")([a-zA-Z0-9- _/\.()]*)(".*)(>)')
        images = []
        for img_rex in rex.findall(self.header):
            images.append(img_rex[3])
        return images

    def first_image(self):
        images = self.get_images()
        if images:
            return images[0]
        return None

    def get_comments(self):
        return self.articlecomment_set.filter(active=True)

    def get_sections(self):
        return self.sections.distinct()

    def get_sections_display(self):
        if self.sections.exists():
            return u'%s' % self.sections.all()[0]
        return u' - '
    get_sections_display.short_description = u'Seção'
signals.pre_save.connect(slug_pre_save, sender=Article)
@receiver(signals.pre_save, sender=Article)
def article_sendemail_aprovacao(sender, instance, raw, using, *args, **kwargs):
    if instance.pk:
        ant = Article.objects.get(pk=instance.pk)
        if not instance.is_active and ant.is_active:
            sendmail(
                subject=u'Existe um artigo para ser aprovado',
                to = list(User.objects.filter(groups__name=u'Editor').values_list('email', flat=True)),
                params = {
                    'article': instance,
                    'HOST': settings.SITE_HOST,
                },
                template = 'emails/article.html',
            )


class ArticleArchive(models.Model):
    class Meta:
        ordering = ('updated_at', )
        verbose_name = u'Versão do Artigo'
        verbose_name_plural = u'Versões dos Artigos'

    article = models.ForeignKey(Article, verbose_name=u'Artigo')
    header = models.TextField(u'Chamada', null=True, blank=True)
    content = models.TextField(u'Conteúdo', null=True, blank=True)
    updated_at = models.DateTimeField(u'Dt.Alteração', auto_now=True)
    user = models.ForeignKey('auth.User', verbose_name=u'Autor')

    def __unicode__(self):
        return u"%s / %s" % (self.article, self.updated_at)


class ArticleComment(models.Model):
    class Meta:
        ordering = ('created_at', )
        verbose_name = u'Comentário'
        verbose_name_plural = u'Comentários'

    article = models.ForeignKey(Article, verbose_name=u'Artigo')
    created_at = models.DateField(u'Dt.Criação', auto_now_add=True)
    author = models.CharField(u'Autor', max_length=60)
    comment = models.TextField(u'Comentário')
    active = models.BooleanField(u'Ativo', default=False)

    def __unicode__(self):
        return u"%s" % (self.author, )

class Menu(MPTTModel):
    name = models.CharField(u'Nome', max_length=50)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', verbose_name=u'Pai')
    link = models.CharField(u'URL', max_length=250, null=True, blank=True)
    section = models.ForeignKey('Section', null=True, blank=True, verbose_name=u'Seção')
    article = ChainedForeignKey(
        Article,
        chained_field='section',
        chained_model_field='sections',
        show_all=False,
        auto_choose=False,
        null=True,
        blank=True,
        default=None,
        verbose_name=u'Artigo'
    )
    is_active = models.BooleanField(u'Está ativo?', default=True)

    objects = ItemManager()

    def __unicode__(self):
        return self.name


    def have_perm(self, user):
        if self.parent:
            return self.parent.have_perm(user)
        if self.section:
            return self.section.have_perm(user)
        if self.article:
            return self.article.have_perm(user)
        return True

    def get_link(self):
        link = None
        if self.link:
            link = self.link
        elif self.article:
            link = self.article.get_absolute_url()
        elif self.section:
            link = self.section.get_absolute_url()
        return link


class Section(models.Model):
    class Meta:
        verbose_name = u'Seção'
        verbose_name_plural = u'Seções'
        ordering = ['order', 'title']

    title = models.CharField(u'Título', max_length=250)
    slug = models.SlugField(u'Slug', max_length=250, blank=True)
    header = models.TextField(u'Descrição', null=True, blank=True)
    keywords = models.TextField(u'Palavras Chaves', null=True, blank=True, default=None)
    order = models.PositiveIntegerField(u'Ordem', default=1, db_index=True, help_text=u'0 para que a seção não apareça em nenhuma listagem.')

    views = models.IntegerField(default=0)
    conversions = models.IntegerField(default=0)

    articles = models.ManyToManyField(Article, through='SectionItem', null=True, blank=True)
    slug_conf = {'field': 'slug', 'from': 'title'}

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('section', kwargs={'slug': self.slug})

    def get_conversion_url(self):
        link = reverse('link', kwargs={'section_slug': self.slug})
        return u'%s%s?next=' % (settings.SITE_HOST, link)
    get_conversion_url.short_description = u'URL de conversão'

    def have_perm(self, user):
        if not self.permissao_set.count():
            return True
        if user.is_superuser:
            return True
        if user.groups.filter(pk__in=self.permissao_set.values_list('pk', flat=True)).exists():
            return True
        return False

    def get_articles(self, query=None):
        articles = self.articles.filter(is_active=True).order_by('sectionitem__order', '-created_at', '-updated_at')
        if query:
            articles = articles.filter(title__icontains=query).order_by('sectionitem__order', '-created_at', '-updated_at')
        return articles

    def num_articles(self):
        return self.get_articles().count()
    num_articles.short_description = u'Nº de artigos'
signals.pre_save.connect(slug_pre_save, sender=Section)


class SectionItem(models.Model):
    class Meta:
        verbose_name = u'Artigo da seção'
        verbose_name_plural = u'Artigos da seção'
        ordering = ['order']

    section = models.ForeignKey(Section, verbose_name=u'Seção')
    article = models.ForeignKey(Article, verbose_name=u'Artigo')
    order = models.PositiveIntegerField(u'Ordem', default=1, db_index=True)

    def __unicode__(self):
        return self.article.title

    def display_article_link(self):
        return u'<a href="%s">%s</a>' % (reverse('admin:cms_article_change', args=(self.article.pk, )), self.article)
    display_article_link.allow_tags = True
    display_article_link.short_description = u'Article'

    def display_article_created_at(self):
        return self.article.created_at.strftime('%d/%m/%Y')
    display_article_created_at.short_description = u'criado em'


class Permissao(models.Model):
    class Meta:
        verbose_name = u'Permissão'
        verbose_name_plural = u'Permissões'

    section = models.ForeignKey(Section)
    group = models.ForeignKey(Group)

    def __unicode__(self):
        return u'%s/%s' % (self.section, self.group)


class GroupType(models.Model):
    class Meta:
        verbose_name = u'Tipo de Grupo'
        verbose_name_plural = u'Tipos de Grupo'
        ordering = ('order', )

    name = models.CharField(u'Nome', max_length=80)
    order = models.PositiveIntegerField(u'Ordem', default=1)

    def __unicode__(self):
        return u'%s' % self.name


class GroupItem(models.Model):
    class Meta:
        verbose_name = u'Item'
        verbose_name_plural = u'Itens'
        ordering = ('grouptype__name', 'group__name', )

    grouptype = models.ForeignKey(GroupType)
    group = models.ForeignKey(Group)

    def __unicode__(self):
        return u'%s' % self.group


REDIRECT_TYPE_CHOICES = (
    ('M', u'MOVED'),
    ('H', u'HOTLINK'),
)
class URLMigrate(models.Model):
    class Meta:
        verbose_name = u'Migração de URL'
        verbose_name_plural = u'Migração de URLs'

    old_url = models.CharField(u'URL antiga', max_length=250, db_index=True)
    new_url = models.CharField(u'URL nova', max_length=250)
    dtupdate = models.DateTimeField(u'Última atualização', auto_now_add=True, auto_now=True, editable=False)
    views = models.IntegerField(u'Visitas', default=0, editable=False)
    redirect_type = models.CharField(u'Tipo', max_length=1, choices=REDIRECT_TYPE_CHOICES)
    obs = models.TextField(u'Observação', blank=True, null=True)

    def __unicode__(self):
        return u'%s -> %s' % (self.old_url, self.new_url, )


class FileDownload(models.Model):
    class Meta:
        verbose_name = u'Arquivo para download'
        verbose_name_plural = u'Arquivos para download'

    uuid = UUIDField(auto=True)
    title = models.CharField(u'Título', max_length=250)
    file = models.FileField(u'Arquivo', upload_to='uploads')
    count = models.IntegerField(u'Downloads', default=0)
    expires_at = models.DateTimeField(u'Data de expiração', null=True, blank=True, default=None)
    create_article = models.BooleanField('Criação do Artigo', default=False)
    article = models.ForeignKey(Article, blank=True, null=True)

    def is_expired(self):
        if self.expires_at:
            return self.expires_at < timezone.now()
        return False

    def get_absolute_url(self):
        return reverse('download', kwargs={'file_uuid': self.uuid,})

    def download_url(self):
        return u'%s%s' % (settings.SITE_HOST, self.get_absolute_url(), )
    download_url.short_description = u'URL de download'

    def article_url(self):
        if self.article:
            return reverse('admin:cms_article_change', args=(self.article.pk, ))
        return u'-'
    article_url.short_description = u'URL do artigo'

    def __unicode__(self):
        return self.title


STATUS_EMAIL = (
    ("A", u'Aguardando envio manual...'),
    ("S", u'Enviando...'),
    ("R", u'Re-enviando'),
    ("E", u'Erro ao enviar'),
    ("K", u'Enviado'),
)
class EmailAgendado(models.Model):
    class Meta:
        ordering = ('-date', )

    subject = models.CharField(max_length=255, default="")
    status = models.CharField(max_length=1, choices=STATUS_EMAIL, default="S")
    date = models.DateTimeField(default=datetime.now)
    to = ListField()
    html = models.TextField()

    def send_email(self):
        resendmail_email_agendado(self)

    def __unicode__(self):
        return u"%s" % self.id


RECURSOS = (
    (u'EMAIL', u'Envio de email automático'),
    (u'SITE_NAME', u'Nome do Site'),
    (u'ROBOTS', u'Permite busca pelo Google'),
    (u'COMMENT_P', u'Texto para comentários privados'),
    (u'COMMENT', u'Texto para comentários'),
    (u'SIGNUP', u'Permite cadastro de usuários'),
    (u'EMAILADMIN', u'Quem recebe avisos de novos usuários'),
)
class Recurso(models.Model):

    recurso = models.CharField(u"Parâmetro", max_length=10, choices=RECURSOS, unique=True)
    valor = models.TextField(u"Valor", blank=True, null=True)
    ativo = models.BooleanField(u"Ativo?", default=True)

    class Meta:
        verbose_name = u'Parâmetro do Site'
        verbose_name_plural = u'Parâmetros do Site'

    def __unicode__(self):
        return u"%s" % self.get_recurso_display()
