# coding:utf-8
from django.db.models import Q
from django.contrib import admin, messages
from django.http import HttpResponseRedirect, HttpResponse
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.shortcuts import get_object_or_404

from django.core.exceptions import PermissionDenied

from django.contrib.admin import helpers
from django.db import models, transaction
from django.contrib.admin.util import unquote, flatten_fieldsets
from django.forms.models import modelform_factory
from django import forms
from functools import partial

from django.db import models
from django.utils.text import get_text_list
from django.utils.translation import ugettext as _
from django.utils.encoding import force_unicode
from datetime import datetime

from mptt.admin import MPTTModelAdmin
from treeadmin.admin import TreeAdmin
from ckeditor.widgets import CKEditorWidget
from poweradmin.admin import PowerModelAdmin, PowerButton

from models import Menu, Section, Article, SectionItem, URLMigrate, \
    FileDownload, ArticleArchive, ArticleComment, EmailAgendado, Recurso, \
    Permissao, GroupType, GroupItem, ArticleAttribute

from forms import CustomGroupForm, PowerArticleForm

from django.core.files.base import ContentFile
import os, zipfile, StringIO


class FileDownloadAdmin(PowerModelAdmin):
    list_display = ['title', 'file', 'count', 'expires_at']
    readonly_fields = ['count', 'download_url',]
    fieldsets = (
        (None, {
            'fields': ['title', 'file', 'expires_at', 'create_article', 'count', 'download_url', ]
        }),
    )

    def get_buttons(self, request, object_id):
        buttons = super(FileDownloadAdmin, self).get_buttons(request, object_id)
        if object_id:
            obj = self.get_object(request, object_id)
            if obj.article:
                buttons.append(PowerButton(url=obj.article_url(), label='Artigo'))
        return buttons

    def save_model(self, request, obj, form, change):
        super(FileDownloadAdmin, self).save_model(request, obj, form, change)
        if obj.create_article and not obj.article:
            article = Article(
                title=u'Download %s' % obj.title,
                content=u'<a href="%s">Download</a>' % obj.get_absolute_url(),
                author=request.user,
            )
            article.save()
            obj.article = article
            obj.save()

admin.site.register(FileDownload, FileDownloadAdmin)


class URLMigrateAdmin(PowerModelAdmin):
    list_display = ['old_url', 'new_url', 'redirect_type', 'dtupdate', 'views']

    class Media:
        js = ('js/custom_admin.js', )
admin.site.register(URLMigrate, URLMigrateAdmin)


class SectionItemCreateInline(admin.TabularInline):
    model = SectionItem
    extra = 1

    def queryset(self, request):
        return super(SectionItemCreateInline, self).queryset(request).none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'article':
            kwargs['queryset'] = Article.objects.filter(is_active=True)
            return db_field.formfield(**kwargs)
        return super(SectionItemCreateInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
class SectionItemActiveInline(admin.TabularInline):
    model = SectionItem
    extra = 0
    readonly_fields = ['display_article_link', 'section', 'display_article_created_at']
    fields = ['display_article_link', 'section', 'order', 'display_article_created_at']

    def has_add_permission(self, request):
        return False
class PermissaoSectionInline(admin.TabularInline):
    model = Permissao
    extra = 1

class SectionAdmin(PowerModelAdmin):
    list_display = ['title', 'views', 'conversions', 'num_articles', 'order']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('order', )
    fieldsets_superuser = (
        (None, {
            'fields': ['title', 'slug', 'header', 'keywords', 'order', 'template', ]
        }),
    )
    fieldsets = (
        (None, {
            'fields': ['title', 'slug', 'header', 'keywords', 'order']
        }),
    )
    inlines = [SectionItemActiveInline, SectionItemCreateInline, PermissaoSectionInline]

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return self.fieldsets_superuser
        return self.fieldsets

    def get_form(self, request, obj=None, **kwargs):
        defaults = {
            "form": self.form if not obj else forms.ModelForm,
            "fields": flatten_fieldsets(self.get_fieldsets(request, obj)),
            "exclude": self.get_readonly_fields(request, obj),
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return modelform_factory(self.model, **defaults)

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ['header']:
            kwargs['widget'] = CKEditorWidget()

        return super(SectionAdmin, self).formfield_for_dbfield(db_field, **kwargs)
admin.site.register(Section, SectionAdmin)


class GroupItemGroupTypeInline(admin.TabularInline):
    model = GroupItem
    extra = 1

class GroupTypeAdmin(PowerModelAdmin):
    list_display = ['name', 'order']
    search_fields = ('name', )
    list_editable = ('order', )
    fieldsets = (
        (None, {
            'fields': ['name', 'order', ]
        }),
    )
    inlines = [GroupItemGroupTypeInline, ]
admin.site.register(GroupType, GroupTypeAdmin)


class SectionItemInline(admin.TabularInline):
    model = SectionItem
    extra = 0
    verbose_name_plural = u'Seções'
class ArticleAttributeInline(admin.TabularInline):
    model = ArticleAttribute
    extra = 1
class ArticleCommentInline(admin.TabularInline):
    model = ArticleComment
    extra = 0
    fields = ('created_at', 'author', 'comment', 'active')
    readonly_fields = ('created_at', 'author', 'comment')
class ArticleAdmin(PowerModelAdmin):
    list_display = ('title', 'slug', 'get_sections_display', 'created_at', 'is_active', 'allow_comments', 'views', 'conversions', )
    list_editable = ('is_active', )
    multi_search = (
       ('q1', 'Título', ['title']),
       ('q2', 'Conteúdo', ['content']),
       ('q3', 'Palavras Chaves', ['keywords']),
       ('q4', 'Seção', ['sectionitem__section__title']),
    )
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': [
                ('title', 'slug'), 'header', 'content', 'keywords', 'created_at', 'author', 'is_active', 'allow_comments',
            ]
        }),
    )
    actions = ('reset_views', )
    inlines = (SectionItemInline, ArticleAttributeInline, ArticleCommentInline, )

    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        if request.user.has_perm('cms.manage_articles') and not (request.user.is_superuser or request.user.groups.filter(name=u'Editor').exists()):
            return HttpResponseRedirect(reverse('admin:cms_article_add_power'))
        return super(ArticleAdmin, self).add_view(request, form_url, extra_context)

    @transaction.commit_on_success
    def change_view(self, request, object_id, form_url='', extra_context=None):
        if request.user.has_perm('cms.manage_articles') and not (request.user.is_superuser or request.user.groups.filter(name=u'Editor').exists()):
            return HttpResponseRedirect(reverse('admin:cms_article_change_power', args=(object_id, )))
        return super(ArticleAdmin, self).change_view(request, object_id, form_url, extra_context)

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ['header', 'content']:
            kwargs['widget'] = CKEditorWidget()
        return super(ArticleAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'author':
            kwargs['initial'] = request.user.id
            kwargs['queryset'] = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
            return db_field.formfield(**kwargs)
        return super(ArticleAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def queryset(self, request):
        qs = super(ArticleAdmin, self).queryset(request)
        if request.user.has_perm('cms.manage_articles') and not (request.user.is_superuser or request.user.groups.filter(name=u'Editor').exists()):
            qs = qs.filter(author=request.user)
        return qs

    def clone(self, request, id):
        article_clone = Article.objects.get(pk=id)
        article_clone.pk = None
        article_clone.slug = None
        article_clone.views = 0
        article_clone.conversions = 0
        article_clone.created_at = datetime.now()
        article_clone.save()

        self.log_addition(request, article_clone)

        for si in SectionItem.objects.filter(article__pk=id):
            si_clone = SectionItem(
                section=si.section,
                article=article_clone,
                order=si.order
            )
            si_clone.save()
        return HttpResponseRedirect(reverse('admin:cms_article_change', args=(article_clone.id,)))

    @transaction.commit_on_success
    def add_power_view(self, request, form_url='', extra_context=None):
        model = self.model
        opts = model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = PowerArticleForm
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES)
            if form.is_valid():
                new_object = self.save_form(request, form, change=False)
                new_object.is_active = False

                if request.FILES.get('upload'):
                    # Salvar imagem, usando a view do ckeditor
                    from ckeditor.views import upload

                    url = upload(request).content
                    new_object.header = u'<img src="%s" style="width: 50px; height: 37px;"/>%s' % (url, new_object.header, )
                    new_object.content = u'<img src="%s" style="width: 270px; height: 152px; margin: 10px; float: left;"/>%s' % (url, new_object.content, )

                # Ajustar html
                new_object.header = u'<p>%s</p>' % u"</p><p>".join(new_object.header.split('\n'))
                new_object.content = u'<p>%s</p>' % u"</p><p>".join(new_object.content.split('\n'))

                self.save_model(request, new_object, form, False)
                self.log_addition(request, new_object)

                messages.info(request, u'O artigo foi gravado com sucesso e já foi enviado para aprovação.')
                form = ModelForm()
        else:
            form = ModelForm()

        fieldsets = (
            (None, {
                'fields': [('title', 'slug'), 'header', 'content', 'upload', ]
            }),
        )
        adminForm = helpers.AdminForm(form, list(fieldsets), {'slug': ('title',)}, [], model_admin=self)
        media = self.media + adminForm.media

        context = {
            'title': u'Adicionar Artigo',
            'adminform': adminForm,
            'is_popup': "_popup" in request.REQUEST,
            'show_delete': False,
            'media': media,
            'inline_admin_formsets': [],
            'errors': helpers.AdminErrorList(form, []),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)

    @transaction.commit_on_success
    def change_power_view(self, request, object_id, form_url='', extra_context=None):
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        ModelForm = PowerArticleForm
        form = ModelForm(instance=obj)
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                new_object = self.save_form(request, form, change=True)
                new_object.is_active = False
                self.save_model(request, new_object, form, True)

                change_message = self.construct_change_message(request, form, [])
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        fieldsets = (
            (None, {
                'fields': [('title', 'slug'), 'header', 'content', 'upload', ]
            }),
        )
        adminForm = helpers.AdminForm(form, list(fieldsets), {'slug': ('title',)}, [], model_admin=self)
        media = self.media + adminForm.media

        context = {
            'title': u'Editar %s' % obj,
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST,
            'media': media,
            'show_delete': False,
            'inline_admin_formsets': [],
            'errors': helpers.AdminErrorList(form, []),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)


    def get_urls(self):
        urls = super(ArticleAdmin, self).get_urls()
        return patterns('',
            url(r'^add-power/$', self.wrap(self.add_power_view), name='cms_article_add_power'),
            url(r'^power/(.+)/$', self.wrap(self.change_power_view), name='cms_article_change_power'),
            url(r'^clone/(?P<id>\d+)/$', self.wrap(self.clone), name='cms_article_clone'),
        ) + urls

    def get_buttons(self, request, object_id):
        buttons = super(ArticleAdmin, self).get_buttons(request, object_id)
        if object_id:
            buttons.append(PowerButton(url=reverse('admin:cms_article_clone', args=(object_id, )), label='Duplicar Artigo'))
            buttons.append(PowerButton(url="%s?article__id__exact=%s" % (reverse('admin:cms_articlearchive_changelist'), object_id), label='Versões'))
        return buttons

    def reset_views(self, request, queryset):
        num_oper = 0
        for rec in queryset:
            rec.views = 0
            rec.conversions = 0
            rec.save()
            num_oper += 1
        self.message_user(request, 'Artigos reiniciados: %d ' % num_oper)
    reset_views.short_description = u'Apagar número de visualizações e conversões'

    def save_model(self, request, obj, form, change):
        #Versionamento
        if change:
            ant = Article.objects.get(pk=obj.pk)
            version = ArticleArchive(
                article=obj,
                user=request.user
            )
            if ant.header != obj.header:
                version.header=obj.header
                version.save()
            if ant.content != obj.content:
                version.content=obj.content
                version.save()

        if not change:
            obj.author = request.user
            obj.save()

            #Versionamento
            ArticleArchive.objects.create(
                article=obj,
                header=obj.header,
                content=obj.content,
                user=request.user
            )
        return super(ArticleAdmin, self).save_model(request, obj, form, change)
admin.site.register(Article, ArticleAdmin)


class ArticleCommentAdmin(PowerModelAdmin):
    list_display = ('article', 'created_at', 'author', 'active', )
    list_filter = ('created_at', 'active', )
    multi_search = (
       ('q1', 'Título', ['article__title']),
       ('q2', 'Seção', ['article__sectionitem__section__title']),
    )
admin.site.register(ArticleComment, ArticleCommentAdmin)


class ArticleArchiveAdmin(PowerModelAdmin):
    list_display = ['article', 'updated_at', 'user', ]
    date_hierarchy = 'updated_at'
    list_filter = ['article', 'updated_at', ]
    multi_search = (
        ('q1', 'Título', ['article__title']),
        ('q2', 'Conteúdo', ['content']),
    )
    readonly_fields = ['article', 'user', 'updated_at', ]

    fieldsets = (
        (None, {
            'fields': ['article', 'user', 'updated_at', 'header', 'content', ]
        }),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ['header', 'content']:
            kwargs['widget'] = CKEditorWidget()
        return super(ArticleArchiveAdmin, self).formfield_for_dbfield(db_field, **kwargs)
admin.site.register(ArticleArchive, ArticleArchiveAdmin)


class MenuAdmin(TreeAdmin):
    list_display = ('name', 'is_active', )
    list_editable = ('is_active', )
admin.site.register(Menu, MenuAdmin)


class EmailAgendadoAdmin(PowerModelAdmin):
    list_display = ('subject', 'to', 'status', 'date')
    date_hierarchy = 'date'
    readonly_fields = ('subject', 'to', 'status', 'date')
    fields = ('subject', 'to', 'status', 'date', 'html')
    actions = ('renviar', )
    multi_search = (
        ('q1', 'Para', ['to',]),
        ('q2', 'Assunto', ['subject',]),
        ('q3', 'Conteúdo', ['html',]),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ['html']:
            kwargs['widget'] = CKEditorWidget()
        return super(EmailAgendadoAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def renviar(self, request, queryset):
        for q in queryset:
            q.send_email()
admin.site.register(EmailAgendado, EmailAgendadoAdmin)


class RecursoAdmin(PowerModelAdmin):
    list_display = ('recurso', 'ativo',)
admin.site.register(Recurso, RecursoAdmin)


### Nova tela do Group ###
admin.site.unregister(Group)

class GroupAdminCustom(PowerModelAdmin, GroupAdmin):
    form = CustomGroupForm
admin.site.register(Group, GroupAdminCustom)
