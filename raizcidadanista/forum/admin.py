# -*- coding:utf-8 -*-
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from models import Grupo, GrupoUsuario, Topico, TopicoOuvinte, Conversa, ConversaCurtida, \
    Proposta, Voto, ConversaMencao, ConversaHistorico, GrupoCategoria
from cadastro.models import Lista

from ckeditor.widgets import CKEditorWidget
from cms.email import sendmail
from poweradmin.admin import PowerModelAdmin, PowerButton


class GrupoCategoriaInline(admin.TabularInline):
    model = GrupoCategoria
    extra = 1
class GrupoUsuarioInline(admin.TabularInline):
    model = GrupoUsuario
    extra = max_num = 0
    fields = readonly_fields = ('usuario', 'admin', )

class GrupoAdmin(PowerModelAdmin):
    list_display = ('nome', 'localizacao', 'tematico', 'privado', )
    list_filter = ('localizacao', 'tematico', )
    multi_search = (
       ('q1', 'Nome', ['nome',]),
    )
    inlines = (GrupoUsuarioInline, GrupoCategoriaInline, )
    fieldsets = (
        (None, {"fields" : ('nome', 'localizacao', 'tematico', 'privado', 'descricao', ),}, ),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name ==  'descricao':
            kwargs['widget'] = CKEditorWidget()
        return super(GrupoAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not extra_context:
            extra_context = {}
        extra_context['listas'] = Lista.objects.filter(status='A')
        return super(GrupoAdmin, self).change_view(request, object_id, form_url, extra_context)

    def importar_lista(self, request, grupo_id):
        grupo = get_object_or_404(Grupo, pk=grupo_id)
        lista = get_object_or_404(Lista, pk=request.POST.get('lista_id'))
        num_usuarios = 0
        for listacadastro in lista.listacadastro_set.all():
            if listacadastro.pessoa.membro.usuario:
                gu, created = GrupoUsuario.objects.get_or_create(grupo=grupo, usuario=listacadastro.pessoa.membro.usuario)
                if created:
                    num_usuarios += 1
                    LogEntry.objects.log_action(
                        user_id = request.user.id,
                        content_type_id = ContentType.objects.get_for_model(grupo).pk,
                        object_id = grupo.pk,
                        object_repr = u'%s' % grupo,
                        action_flag = CHANGE,
                        change_message = u'%s adicionado via rotina "Importar listas".' % listacadastro.pessoa.membro.usuario
                    )

        messages.info(request, u'%s Usuário(s) importada(s) com sucesso da lista %s.' % (num_usuarios, lista, ))
        return HttpResponseRedirect(reverse('admin:forum_grupo_change', args=(grupo_id, )))

    def get_urls(self):
        urls_originais = super(GrupoAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^(?P<grupo_id>\d+)/importar-listas/$', self.wrap(self.importar_lista), name='forum_grupo_importar_lista'),
        )
        return urls_customizadas + urls_originais

    def get_buttons(self, request, object_id):
        buttons = super(GrupoAdmin, self).get_buttons(request, object_id)
        if object_id:
            buttons.append(PowerButton(url='?lightbox[width]=280&lightbox[height]=90#box-importar_lista', attrs={'class': 'historylink lightbox', }, label=u'Importar listas'))
        return buttons
admin.site.register(Grupo, GrupoAdmin)


class TopicoOuvinteTopicoInline(admin.TabularInline):
    model = TopicoOuvinte
    extra = max_num = 0
    readonly_fields = ('ouvinte', 'notificacao', 'dtentrada', 'dtleitura', 'dtnotificacao', )
class ConversaTopicoInline(admin.TabularInline):
    model = Conversa
    extra = max_num = 0
    readonly_fields = ('autor', 'texto', 'dt_criacao', 'arquivo', 'conversa_pai', )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name ==  'texto':
            kwargs['widget'] = CKEditorWidget()
        return super(ConversaTopicoInline, self).formfield_for_dbfield(db_field, **kwargs)
class TopicoAdmin(PowerModelAdmin):
    list_display = ('titulo', 'grupo', 'categoria', 'status', 'dt_criacao', 'dt_ultima_atualizacao', 'visitacoes', )
    list_filter = ('grupo', 'status', 'dt_criacao', 'dt_ultima_atualizacao', )
    multi_search = (
       ('q1', 'Título', ['titulo']),
       ('q2', 'Autor', ['criador__nome']),
    )
    inlines = (ConversaTopicoInline, TopicoOuvinteTopicoInline, )
    fieldsets = (
        (None, {"fields" : ('titulo', 'criador', 'grupo', 'categoria', 'status',),}, ),
    )
admin.site.register(Topico, TopicoAdmin)


class ConversaCurtidaConversaInline(admin.TabularInline):
    model = ConversaCurtida
    extra = 1

class ConversaAdmin(PowerModelAdmin):
    list_display = ('topico', 'autor', 'dt_criacao', 'conversa_pai', 'editada' )
    list_filter = ('dt_criacao', )
    multi_search = (
       ('q1', 'Tópico', ['topico__titulo']),
       ('q2', 'Autor', ['autor__nome']),
    )
    inlines = (ConversaCurtidaConversaInline, )
    fieldsets = (
        (None, {"fields" : ('topico', 'autor', 'texto', 'arquivo', 'conversa_pai', 'editada', 'editor'),}, ),
    )
    readonly_fields = ('topico', 'autor', 'conversa_pai', )

admin.site.register(Conversa, ConversaAdmin)
admin.site.register(ConversaHistorico)


class VotoPropostaInline(admin.TabularInline):
    model = Voto
    extra = 1
    fk_name = 'proposta'
class PropostaAdmin(PowerModelAdmin):
    list_display = ('topico', 'autor', 'dt_criacao', 'dt_encerramento', 'status', 'conversa_pai', 'get_short_absolute_url', )
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