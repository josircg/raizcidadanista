# -*- coding: utf-8 -*-
import operator
from models import UserAdminConfig
from django.db import models
from django.contrib import admin, messages
from django.contrib.admin.util import flatten_fieldsets
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import resolve
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from poweradmin import filters
from django import forms
from django.db import models

from django.utils.text import get_text_list
from django.utils.translation import ugettext as _
from django.utils.encoding import force_unicode

import django.utils.simplejson as simplejson
from django.core.exceptions import ValidationError
from utils.forms import BRDecimalFormField

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

    def formfield_for_dbfield(self, db_field, **kwargs):
        if type(db_field) == models.DecimalField:
            field = super(PowerModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)
            field.localize = True
            field.widget.is_localized = True
            return field
        return super(PowerModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
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
        ordered_objects = opts.get_ordered_objects()

        object_id = obj.id if obj else obj
        buttons = self.get_buttons(request, object_id)

        context.update({
            'buttons': buttons,
            'readonly': readonly,
        })
        return super(PowerModelAdmin, self).render_change_form(request, context, add, change, form_url, obj)

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
                #ManyToManyFields
                try:
                    if type(form.instance._meta.get_field(field)) == models.fields.related.ManyToManyField:
                        value = value.all().values_list('pk', flat=True)
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

    def related_lookup(self, request):
        data = {}
        if request.method == 'GET':
            if request.GET.has_key('object_id'):
                try:
                    obj = self.queryset(request).get(pk=request.GET.get('object_id'))
                    data = {"value": obj.pk, "label": u"%s" % obj}
                except: pass
        return HttpResponse(simplejson.dumps(data), mimetype='application/javascript')

    def filterchain(self, request):
        keywords = {}
        for field, value in request.GET.items():
            if value == '0':
                keywords[str("%s__isnull" % field)] = True
            else:
                keywords[str(field)] = str(value) or None

        results = self.queryset(request).filter(**keywords)
        if not len(keywords):
            results = results.none()

        result = []
        for item in results:
            result.append({'value': item.pk, 'display': unicode(item)})
        result.append({'value': "", 'display': "---------"})
        return HttpResponse(simplejson.dumps(result), mimetype='application/javascript')

    def get_urls(self):
        opts = self.model._meta

        buttons_urls = [url(r'^(\d+)/(%s)/$' % but.flag, self.wrap(self.button_view_dispatcher)) for but in self.buttons]
        buttons_urls.append(url(r'^lookup/related/$', self.wrap(self.related_lookup), name="%s_%s_related_lookup" % (opts.app_label, opts.object_name.lower())))
        buttons_urls.append(url(r'^chained/$', self.wrap(self.filterchain), name="%s_%s_filterchain" % (opts.app_label, opts.object_name.lower())))
        return patterns('', *buttons_urls) + super(PowerModelAdmin, self).get_urls()

    def wrap(self, view):
        from django.utils.functional import update_wrapper
        def wrapper(*args, **kwargs):
            return self.admin_site.admin_view(view)(*args, **kwargs)
        return update_wrapper(wrapper, view)

    def get_buttons(self, request, object_id):
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

        context_data = {
            'multi_search': True,
            'multi_search_keys': multi_search_fields,
            'admin_old_url': admin_old_url,
        }
        self.change_list_template = self.get_changelist_template()
        extra_context.update(context_data)
        return super(PowerModelAdmin, self).changelist_view(request, extra_context)

    def delete_model(self, request, obj):
        try:
            obj.delete()
        except ValidationError as error:
            for msg in error.messages:
                messages.error(request, u'Erro ao remover: %s' % msg)


class PowerButton(object):
    flag = ''  # Usado para URLs fixas do botao, como na versao anterior
    url = ''  # Usado para informar diretamente a URL e assim permitir qualquer URL
    visible = True
    label = 'Label'
    attrs = {'class': 'historylink', }

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_url(self):
        return self.url or (self.flag + '/')
