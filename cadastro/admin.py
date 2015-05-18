# -*- coding:utf-8 -*-
from django.contrib import admin

from models import *

class CirculoMembroInline(admin.TabularInline):
    model = CirculoMembro
    extra = 1
    verbose_name = u'Círculo do Membro'
    verbose_name_plural = u'Círculos do Membro'

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()

        membro = Membro.objects.get(usuario = request.user)
        if request.user.groups.filter(name=u'Comissão').exists() or CirculoMembro.objects.filter(membro=membro,administrador=True).exists():
            return ()
        else:
            return ('administrador',)

class MembroAdmin(admin.ModelAdmin):
    list_filter = ('uf',)
    search_fields = ('nome','email',)
    list_display = ('nome', 'email', 'dtcadastro', 'aprovador',)
    inlines = (CirculoMembroInline,)
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
            return ('usuario', 'facebook_id','aprovador',)

class CirculoEventoInline(admin.TabularInline):
# só permitir alterar o administrador se o usuário também for administrador
    model = CirculoEvento
    extra = 1
    verbose_name = u'Evento do Círculo'
    verbose_name_plural = u'Círculos do Membro'

    def get_readonly_fields(self, request, obj=None):
        if Circulo.objects.filter(circulo=self.circulo, membro__usuario=request.user,administrador=True).count() == 0 and request.user.groups.filter(name=u'Comissão').count() == 0:
            return ('nome','dt_evento','local')
        else:
            return ()

class CirculoAdmin(admin.ModelAdmin):
    list_filter = ('uf',)

#    fieldset_owner = (None, { "fields" : (('titulo','descricao','tipo','uf','municipio','oficial','dtcadastro','site_externo'),) }, )
#    fieldsets = (None, { "fields" : (('titulo','descricao','uf','municipio','site_externo',),)})

#    def get_fieldsets(self, request, obj=None):
#        if request.user.is_superuser:
#            return self.fieldsets_owner
#        return self.fieldsets

    def save_model(self, request, obj, form, change):
        obj.save()
        if not change:
            membro = Membro.objects.get(usuario=request.user)
            admin = CirculoMembro()
            admin.membro = membro
            admin.circulo = obj
            admin.administrador = True
            admin.save()

'''    def get_readonly_fields(self, request, obj=None):
        if CirculoMembro.objects.filter(membro__usuario=request.user,administrador=True).count() == 0 and request.user.groups.filter(name=u'Comissão').count() == 0:

            if self.declared_fieldsets:
                return flatten_fieldsets(self.declared_fieldsets)
            else:
                return list(set(
                    [field.name for field in self.opts.local_fields] +
                    [field.name for field in self.opts.local_many_to_many]
                ))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if CirculoMembro.objects.filter(membro__usuario=request.user).count() == 0 and request.user.groups.filter(name=u'Comissão').count() == 0:
            self.inlines = [CirculoEventoInline,]
        else:
            self.inlines = [CirculoEventoInline,CirculoMembroInline, ]

        self.inline_instances = []
        for inline_class in self.inlines:
            inline_instance = inline_class(self.model, self.admin_site)
            self.inline_instances.append(inline_instance)
        return super(CirculoAdmin, self).change_view(request, object_id, form_url)
'''

admin.site.register(UF)
admin.site.register(Pessoa)
admin.site.register(Circulo, CirculoAdmin)
admin.site.register(Membro, MembroAdmin)
