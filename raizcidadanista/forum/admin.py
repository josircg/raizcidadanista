# -*- coding:utf-8 -*-
from django.contrib import admin
from models import Grupo, GrupoUsuario, Topico, TopicoOuvinte, Conversa, ConversaCurtida, Proposta, Voto

from ckeditor.widgets import CKEditorWidget
from cms.email import sendmail
from poweradmin.admin import PowerModelAdmin, PowerButton


class GrupoUsuarioInline(admin.TabularInline):
    model = GrupoUsuario
    extra = 1
class GrupoAdmin(PowerModelAdmin):
    list_display = ('nome', )
    multi_search = (
       ('q1', 'Nome', ['nome',]),
    )
    inlines = (GrupoUsuarioInline, )
    fieldsets = (
        (None, {"fields" : ('nome', 'descricao', ),}, ),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name ==  'descricao':
            kwargs['widget'] = CKEditorWidget()
        return super(GrupoAdmin, self).formfield_for_dbfield(db_field, **kwargs)
admin.site.register(Grupo, GrupoAdmin)


class TopicoOuvinteTopicoInline(admin.TabularInline):
    model = TopicoOuvinte
    extra = 1
class ConversaTopicoInline(admin.TabularInline):
    model = Conversa
    extra = 1
class TopicoAdmin(PowerModelAdmin):
    list_display = ('titulo', 'grupo', 'status', 'dt_criacao', 'dt_ultima_atualizacao', 'visitacoes', )
    list_filter = ('grupo', 'status', 'dt_criacao', 'dt_ultima_atualizacao', )
    multi_search = (
       ('q1', 'Título', ['titulo']),
       ('q2', 'Autor', ['criador__nome']),
    )
    inlines = (ConversaTopicoInline, TopicoOuvinteTopicoInline, )
    fieldsets = (
        (None, {"fields" : ('titulo', 'criador', 'grupo', 'status',),}, ),
    )
admin.site.register(Topico, TopicoAdmin)


class ConversaCurtidaConversaInline(admin.TabularInline):
    model = ConversaCurtida
    extra = 1
class ConversaAdmin(PowerModelAdmin):
    list_display = ('topico', 'autor', 'dt_criacao', 'conversa_pai', )
    list_filter = ('topico', 'autor', 'dt_criacao', 'conversa_pai', )
    multi_search = (
       ('q1', 'Tópico', ['topico__titulo']),
       ('q2', 'Autor', ['autor__nome']),
    )
    inlines = (ConversaCurtidaConversaInline, )
    fieldsets = (
        (None, {"fields" : ('topico', 'autor', 'texto', 'arquivo', 'conversa_pai', ),}, ),
    )
admin.site.register(Conversa, ConversaAdmin)


class VotoPropostaInline(admin.TabularInline):
    model = Voto
    extra = 1
class PropostaAdmin(PowerModelAdmin):
    list_display = ('topico', 'autor', 'dt_criacao', 'dt_encerramento', 'status', 'conversa_pai', )
    list_filter = ('topico', 'autor', 'dt_criacao', 'dt_encerramento', 'status', 'conversa_pai', )
    multi_search = (
       ('q1', 'Tópico', ['topico__titulo']),
       ('q2', 'Autor', ['autor__nome']),
    )
    inlines = (VotoPropostaInline, )
    fieldsets = (
        (None, {"fields" : ('topico', 'autor', 'texto', 'dt_encerramento', 'arquivo', 'conversa_pai', 'status', ),}, ),
    )
admin.site.register(Proposta, PropostaAdmin)