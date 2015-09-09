# -*- coding:utf-8 -*-
from django.contrib import admin
from django.contrib.admin.util import flatten_fieldsets
from django.forms.models import modelform_factory
from django.http import HttpResponse

from functools import partial

from models import Membro, Circulo, CirculoMembro, CirculoEvento, Pessoa

from poweradmin.admin import PowerModelAdmin, PowerButton

class CirculoMembroMembroInline(admin.TabularInline):
    model = CirculoMembro
    extra = 1
    verbose_name = u'Círculo do Membro'
    verbose_name_plural = u'Círculos do Membro'

class MembroAdmin(PowerModelAdmin):
    list_filter = ('uf', 'filiado',)
    search_fields = ('nome', 'email',)
    list_display = ('nome', 'email', 'dtcadastro', 'filiado', 'aprovador', )
    inlines = (CirculoMembroMembroInline, )
    actions = ('aprovacao',)

    def aprovacao(self, request, queryset):
        contador = 0
        for rec in queryset:
            contador += 1
            if rec.aprovador is None:
                rec.aprovador = request.user
                rec.save()
        self.message_user(request, 'Total de Membros aprovados: %d' % contador)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        else:
            return ('dtcadastro', 'usuario', 'facebook_id', 'aprovador',)

class CirculoMembroCirculoInline(admin.TabularInline):
    model = CirculoMembro
    extra = 1
    verbose_name = u'Membro do Círculo'
    verbose_name_plural = u'Membros do Círculo'

class CirculoEventoCirculoInline(admin.TabularInline):
    model = CirculoEvento
    extra = 0
    verbose_name = u'Evento do Círculo'
    verbose_name_plural = u'Eventos do Círculo'

    def get_readonly_fields(self, request, obj=None):
        if not (CirculoMembro.objects.filter(circulo=obj, membro__usuario=request.user, administrador=True).exists() or request.user.groups.filter(name=u'Comissão').exists()):
            return ('nome', 'dt_evento', 'local')
        else:
            return ()

class CirculoAdmin(PowerModelAdmin):
    list_display = ('titulo', 'tipo', 'uf', 'oficial',)
    list_filter = ('tipo','uf',)
    fieldsets_comissao = (
        (None, {"fields" : ('titulo', 'descricao', 'tipo', 'uf', 'municipio', 'oficial', 'dtcadastro', 'site_externo', 'imagem', 'status', ),},),
    )
    fieldsets = (
        (None, {"fields" : ('titulo', 'descricao', 'uf', 'municipio', 'site_externo', 'dtcadastro'),}, ),
    )
    actions = ('export_csv', )

    def export_csv(self, request, queryset):
        csv = u'"Título";"Município";"UF"\n'
        for q in queryset:
            csv += u'"%(titulo)s";"%(municipio)s";"%(uf)s"\n' % {
                'titulo': q.titulo,
                'municipio': u'%s' % q.municipio,
                'uf': q.uf if q.uf else u'',
            }
        response = HttpResponse(csv, mimetype='application/csv; charset=utf-8', )
        response['Content-Disposition'] = 'filename=circulos.csv'
        return response
    export_csv.short_description = u"Gerar arquivo de exportação"

    def get_fieldsets(self, request, obj=None):
        if request.user.groups.filter(name=u'Comissão').exists() or request.user.is_superuser:
            return self.fieldsets_comissao
        return self.fieldsets

    def get_readonly_fields(self, request, obj=None):
        if not (CirculoMembro.objects.filter(circulo=obj, membro__usuario=request.user, administrador=True).exists() and not request.user.groups.filter(name=u'Comissão').exists()):
            return ()
        else:
            return ('titulo', 'descricao', 'tipo', 'uf', 'municipio', 'dtcadastro', 'site_externo')

    def get_form(self, request, obj=None, **kwargs):
        defaults = {
            "form": self.form,
            "fields": flatten_fieldsets(self.get_fieldsets(request, obj)),
            "exclude": self.get_readonly_fields(request, obj),
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return modelform_factory(self.model, **defaults)

    def save_model(self, request, obj, form, change):
        return super(CirculoAdmin, self).save_model(request, obj, form, change)
#        if not change:
#            try:
#                membro = Membro.objects.get(usuario=request.user)
#                CirculoMembro(
#                    membro = membro,
#                    circulo = obj,
#                    administrador = True,
#                ).save()
#            except Membro.DoesNotExists:
#                return

    def get_inline_instances(self, request, obj=None):
        if request.user.groups.filter(name=u'Comissão').exists() or CirculoMembro.objects.filter(circulo=obj, membro__usuario=request.user, administrador=True).exists():
            self.inlines = [CirculoEventoCirculoInline, CirculoMembroCirculoInline, ]
        else:
            self.inlines = [CirculoEventoCirculoInline,]
        return [inline(self.model, self.admin_site) for inline in self.inlines]

    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name=u'Comissão').exists() or CirculoMembro.objects.filter(circulo=obj, membro__usuario=request.user, administrador=True).exists():
            return ()
        else:
            return flatten_fieldsets(self.get_fieldsets(request, obj))

admin.site.register(Circulo, CirculoAdmin)
admin.site.register(CirculoEvento)
admin.site.register(Membro, MembroAdmin)
admin.site.register(Pessoa)
