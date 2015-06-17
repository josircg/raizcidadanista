# -*- coding:utf-8 -*-
from django.contrib import admin
from django.contrib.admin.util import flatten_fieldsets

from models import Membro, Circulo, CirculoMembro, CirculoEvento, Pessoa


class CirculoMembroMembroInline(admin.TabularInline):
    model = CirculoMembro
    extra = 1
    verbose_name = u'Círculo do Membro'
    verbose_name_plural = u'Círculos do Membro'

class MembroAdmin(admin.ModelAdmin):
    list_filter = ('uf',)
    search_fields = ('nome','email',)
    list_display = ('nome', 'email', 'dtcadastro', 'aprovador',)
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
            return ('dtcadastro',' usuario', 'facebook_id', 'aprovador',)

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

class CirculoAdmin(admin.ModelAdmin):
    list_filter = ('uf',)
    list_fields = ('titulo','tipo','uf','oficial',)

    fieldsets_owner = (
        (None, {"fields" : ('titulo', 'descricao', 'tipo', 'uf', 'municipio', 'oficial', 'dtcadastro', 'site_externo',),},),
    )
    fieldsets = (
        (None, {"fields" : ('titulo', 'descricao', 'uf', 'municipio', 'site_externo', ),}, ),
    )

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser or obj==None:
            return self.fieldsets_owner
        return self.fieldsets

    def save_model(self, request, obj, form, change):
        obj.save()
        if not change:
            membro = Membro.objects.get(usuario=request.user)
            CirculoMembro(
                membro = membro,
                circulo = obj,
                administrador = True,
            ).save()

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
