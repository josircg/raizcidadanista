# -*- coding: utf-8 -*-
import operator
from models import UserAdminConfig
from django.db import models
from django.contrib import admin, messages
from django.contrib.admin.util import flatten_fieldsets
from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import resolve
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from poweradmin import filters
from django import forms

from django.utils.text import get_text_list
from django.utils.translation import ugettext as _
from django.utils.encoding import force_unicode

'''
 Features:
 - novo filtro multi_search
 - list_filter no cabeçalho da página ao invés de ficar na lateral

 multi_search sintaxe:
     multi_search = (
        ('q1', 'Nome', ['disciplina__nome']),
        ('q2', 'E-mail', ['email']),
    )
'''


POWERADMIN_USE_WIKI = getattr(settings, 'POWERADMIN_USE_WIKI', False)
POWERADMIN_WIKI_ARTICLE_URL = getattr(settings, 'POWERADMIN_WIKI_ARTICLE_URL', '/wiki/{path}/')


#Trim solution
class _BaseForm(object):
    def clean(self):
        for field in self.cleaned_data:
            if isinstance(self.cleaned_data[field], basestring):
               self.cleaned_data[field] = self.cleaned_data[field].strip()
        return super(_BaseForm, self).clean()

class BaseModelForm(_BaseForm, forms.ModelForm):
    pass


class PowerModelAdmin(admin.ModelAdmin):
    buttons = []
    active_report = False  # flag para ativar ou desativar o report
    multi_search = []
    list_select_related = True
    multi_search_query = {}
    queryset_filter = {}
    form = BaseModelForm

    def __init__(self, model_class, *args, **kwargs):
        if not hasattr(self, 'report_header_detailed'):
            self.report_header_detailed = u'<h1>Relatório</h1>'

        if not hasattr(self, 'fieldsets_report'):
            if hasattr(self, 'list_display') and self.list_display:
                if len(self.list_display) == 1 and '__str__' in self.list_display:
                    self.active_report = False  # nao foi setado o list_display
            else:
                self.active_report = False  # foi setado o list_display para vazio

            self.fieldsets_report = [
                (u'Relatório', {'fields': self.list_display, }, ),
            ]

        return super(PowerModelAdmin, self).__init__(model_class, *args, **kwargs)

    def get_actions(self, request):
        actions = super(PowerModelAdmin, self).get_actions(request)
        if self.active_report:
            from report.actions import report_generic_detailed
            actions['report_generic_detailed'] = (
                report_generic_detailed,
                'report_generic_detailed',
                report_generic_detailed.short_description)
        #Ajustes no log do action delete_selected
        from poweradmin.actions import delete_selected
        actions['delete_selected'] = (delete_selected, 'delete_selected', delete_selected.short_description)
        return actions

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        Método padrão do ModelAdmin, cutomizado para pegar o template do
        get_change_form_template() criado para classe.
        """
        #Verifica se a tela é readonly
        readonly = False
        readonly_fields = list(self.get_readonly_fields(request, obj))
        fields = list(flatten_fieldsets(self.get_fieldsets(request, obj)))
        if set(fields) == set(readonly_fields).intersection(set(fields)):
            readonly = True
        
        for inline in context['inline_admin_formsets']:
            if set(flatten_fieldsets(inline.fieldsets)) != set(inline.readonly_fields).intersection(set(flatten_fieldsets(inline.fieldsets))):
                readonly = False

        opts = self.model._meta
        app_label = opts.app_label
        ordered_objects = opts.get_ordered_objects()

        object_id = obj.pk if obj else obj
        buttons = self.get_buttons(request, object_id)

        if POWERADMIN_USE_WIKI:
            path = '{0}-{1}'.format(app_label.lower(), opts.object_name.lower())
            from wiki.models import Article, ArticleRevision, URLPath
            from django.contrib.sites.models import get_current_site

            if not URLPath.objects.filter(slug=path).count():
                if not URLPath.objects.count():
                    URLPath.create_root(
                        site=get_current_site(request),
                        title=u'Root',
                        content=u"",
                        request=request
                    )
                root = URLPath.objects.order_by('id')[0]

                URLPath.create_article(
                    root,
                    path,
                    site=get_current_site(request),
                    title=path,
                    content=u"",
                    user_message=u"",
                    user=request.user,
                    ip_address=request.META['REMOTE_ADDR'],
                    article_kwargs={
                        'owner': request.user
                    }
                )
            buttons.append(PowerButton(url=POWERADMIN_WIKI_ARTICLE_URL.format(path=path), label=u'Ajuda'))

        context.update({
            'buttons': buttons,
            'add': add,
            'change': change,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj),
            'has_delete_permission': self.has_delete_permission(request, obj),
            'has_file_field': True,  # FIXME - this should check if form or formsets have a FileField,
            'has_absolute_url': hasattr(self.model, 'get_absolute_url'),
            'ordered_objects': ordered_objects,
            'form_url': mark_safe(form_url),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model(self.model).id,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
            'root_path': getattr(self.admin_site, 'root_path', None),
            'readonly': readonly,
        })
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response(self.get_change_form_template(), context, context_instance=context_instance)

    # Método que escolhe o template para renderizar o formulário de edição
    # Caso não exista formulários customizados retorna o change_form_template da classe.
    def get_change_form_template(self):
        opts = self.model._meta
        app_label = opts.app_label

        return [
            self.change_form_template,
            "admin/%s/%s/change_form.html" % (app_label, opts.object_name.lower()),
            "admin/%s/change_form.html" % app_label,
            "admin/edit_form.html",
            "admin/change_form.html",
        ]

    def construct_change_message(self, request, form, formsets):
        """
        Construct a change message from a changed object.
        """
        change_message = []
        if form.changed_data:
            changed_data_msg = []
            for field in form.changed_data:
                initial=form.initial.get(field)
                try: value=getattr(form.instance, field)
                except: value=form.initial.get(field)
                #ForeignKey
                try:
                    if type(form.instance._meta.get_field(field)) == models.fields.related.ForeignKey:
                        initial = getattr(form.instance, field).__class__.objects.get(pk=initial)
                except: pass
                #Choices
                try:
                    if type(form.instance._meta.get_field(field)) == models.fields.CharField and hasattr(form.instance._meta.get_field(field), 'choices'):
                        try: initial = dict(type(form.instance)._meta.get_field(field).get_choices())[initial]
                        except: pass
                        try: value = dict(type(form.instance)._meta.get_field(field).get_choices())[value]
                        except: pass
                except: pass
                if initial != value:
                    changed_data_msg.append(u'%s de %s para %s' % (force_unicode(field), force_unicode(initial), force_unicode(value)))
            if changed_data_msg:
                change_message.append(_(u'Changed %s.') % get_text_list(changed_data_msg, _('and')))

        if formsets:
            for formset in formsets:
                for added_object in formset.new_objects:
                    change_message.append(_(u'Added %(name)s "%(object)s".')
                                          % {'name': force_unicode(added_object._meta.verbose_name),
                                             'object': force_unicode(added_object)})
                for changed_object, changed_fields in formset.changed_objects:
                    change_message.append(_(u'Changed %(list)s for %(name)s "%(object)s".')
                                          % {'list': get_text_list(changed_fields, _('and')),
                                             'name': force_unicode(changed_object._meta.verbose_name),
                                             'object': force_unicode(changed_object)})
                for deleted_object in formset.deleted_objects:
                    change_message.append(_(u'Deleted %(name)s "%(object)s".')
                                          % {'name': force_unicode(deleted_object._meta.verbose_name),
                                             'object': force_unicode(deleted_object)})
        change_message = ' '.join(change_message)
        return change_message or _(u'No fields changed.')

    def get_changelist_template(self):
        opts = self.model._meta
        app_label = opts.app_label

        return [
            'admin/%s/%s/change_list_multi_search.html' % (app_label, opts.object_name.lower()),
            'admin/%s/change_list_multi_search.html' % app_label,
            'admin/change_list_multi_search.html'
        ]

    def button_view_dispatcher(self, request, object_id, command):
        obj = self.model._default_manager.get(pk=object_id)
        return getattr(self, command)(request, obj)  \
            or HttpResponseRedirect(request.META['HTTP_REFERER'])

    def get_urls(self):
        buttons_urls = [url(r'^(\d+)/(%s)/$' % but.flag, self.wrap(self.button_view_dispatcher)) for but in self.buttons]
        return patterns('', *buttons_urls) + super(PowerModelAdmin, self).get_urls()

    def wrap(self, view):
        from django.utils.functional import update_wrapper
        def wrapper(*args, **kwargs):
            return self.admin_site.admin_view(view)(*args, **kwargs)
        return update_wrapper(wrapper, view)

    def get_buttons(self, request, object_id=None):
        return [b for b in self.buttons if b.visible]

    def get_changelist(self, request, **kwargs):
        from views import PowerChangeList
        return PowerChangeList

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['buttons'] = self.get_buttons(request, None)

        c_url = resolve(request.path_info)

        if c_url.namespace:
            url_name = '%s:%s' % (c_url.namespace, c_url.url_name)
        else:
            url_name = '%s' % c_url.url_name

        try:
            admin_config = UserAdminConfig.objects.filter(user=request.user, url_name=url_name)[0]
            admin_old_url = admin_config.url_full_path

            admin_config.url_name = url_name
            admin_config.url_full_path = request.get_full_path()
            admin_config.save()
        except IndexError:
            admin_old_url = None
            admin_config = UserAdminConfig.objects.create(
                user=request.user,
                url_name=url_name,
                url_full_path=request.get_full_path(),
            )

        if admin_old_url == request.get_full_path():
            admin_old_url = None

        extra_context['admin_old_url'] = admin_old_url

        opts = self.model._meta
        app_label = opts.app_label

        multi_search_fields = []
        for field_opts in self.multi_search:
            attributes = {
                'size': '40',
            }

            if len(field_opts) == 4:
                attributes.update(field_opts[3])

            multi_search_fields.append({
                'name': field_opts[0],
                'label': field_opts[1],
                'value': request.GET.get(field_opts[0], ''),
                'attributes': ' '.join(['%s="%s"' % (k, v) for k, v in attributes.items()]),
            })

        buttons = self.get_buttons(request, None)

        if POWERADMIN_USE_WIKI:
            path = '{0}-{1}'.format(app_label.lower(), opts.object_name.lower())
            from wiki.models import Article, ArticleRevision, URLPath
            from django.contrib.sites.models import get_current_site

            if not URLPath.objects.filter(slug=path).count():
                if not URLPath.objects.count():
                    URLPath.create_root(
                        site=get_current_site(request),
                        title=u'Root',
                        content=u"",
                        request=request
                    )
                root = URLPath.objects.order_by('id')[0]

                URLPath.create_article(
                    root,
                    path,
                    site=get_current_site(request),
                    title=path,
                    content=u"",
                    user_message=u"",
                    user=request.user,
                    ip_address=request.META['REMOTE_ADDR'],
                    article_kwargs={
                        'owner': request.user
                    }
                )
            buttons.append(PowerButton(url=POWERADMIN_WIKI_ARTICLE_URL.format(path=path), label=u'Ajuda', attrs={'target': '_blank'}))

        context_data = {
            'buttons': buttons,
            'multi_search': True,
            'multi_search_keys': multi_search_fields,
            'admin_old_url': admin_old_url,
        }
        self.change_list_template = self.get_changelist_template()
        extra_context.update(context_data)
        return super(PowerModelAdmin, self).changelist_view(request, extra_context)


class PowerButton(object):
    flag = ''  # Usado para URLs fixas do botao, como na versao anterior
    url = ''  # Usado para informar diretamente a URL e assim permitir qualquer URL
    visible = True
    label = 'Label'
    attrs = {}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_url(self):
        return self.url or (self.flag + '/')
