# -*- coding:utf-8 -*-
from django.contrib import admin, messages
from django.contrib.admin.util import flatten_fieldsets
from django.forms.models import modelform_factory
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

from datetime import datetime
from functools import partial
import csv

from forms import MembroImport
from models import Membro, Circulo, CirculoMembro, CirculoEvento, Pessoa

from municipios.models import UF, Municipio
from cms.email import sendmail
from poweradmin.admin import PowerModelAdmin, PowerButton


class PessoaAdmin(PowerModelAdmin):
    list_display = ('nome', 'email', 'status_email', 'dtcadastro', )
    search_fields = ('nome', 'email',)
    list_filter = ('uf', 'dtcadastro')
    actions = ('validar_email', )

    def validar_email(self, request, queryset):
        contador = 0
        for rec in queryset:
            if rec.status_email == 'N':
                contador += 1
                sendmail(
                    subject=u'Raiz Movimento Cidadanista - Validação de email',
                    to=[rec.email, ],
                    template='emails/validar-email.html',
                    params={
                        'pessoa': rec,
                        'SITE_HOST': settings.SITE_HOST,
                    },
                )
        self.message_user(request, 'Total de emails enviados para aprovação: %d' % contador)
    validar_email.short_description = u'Validar Emails'

class CirculoMembroMembroInline(admin.TabularInline):
    model = CirculoMembro
    extra = 1
    verbose_name = u'Círculo do Membro'
    verbose_name_plural = u'Círculos do Membro'

class MembroAdmin(PowerModelAdmin):
    list_filter = ('uf', 'filiado',)
    search_fields = ('nome', 'email',)
    list_display = ('nome', 'email', 'municipio', 'dtcadastro', 'aprovador', )
    inlines = (CirculoMembroMembroInline, )
    actions = ('aprovacao', )

    def aprovacao(self, request, queryset):
        contador = 0
        for rec in queryset:
            if rec.aprovador is None:
                contador += 1
                rec.aprovador = request.user
                rec.save()
                sendmail(
                    subject=u'Seja bem-vindo à Raiz Movimento Cidadanista',
                    to=[rec.email, ],
                    template='emails/bemvindo-colaborador.html',
                    params={
                    },
                )
        self.message_user(request, 'Total de Membros aprovados: %d' % contador)
    aprovacao.short_description = u'Aprovação'

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        else:
            return ('dtcadastro', 'usuario', 'facebook_id', 'aprovador',)

    def import_membros(self, request, form_class=MembroImport, template_name='admin/core/membro/import.html'):
        if not request.user.is_superuser:
            raise PermissionDenied()

        form = form_class()
        if request.method == 'POST':
            form = form_class(request.POST, request.FILES)
            if form.is_valid():
                var = {
                    'dtcadastro': 0, 'nome': 1, 'uf': 2, 'municipio': 3, 'email': 4, 'celular': 5, 'operadora_celular': 6, 'residencial': 7,
                    'atividade_profissional': 8, 'dtnascimento': 9, 'rg': 10, 'titulo_eleitoral': 11, 'zona_secao_eleitoral': 12, 'municipio_eleitoral': 13,
                    'uf_eleitoral': 14, 'foi_filiacao_partidaria': 15, 'filiacao_partidaria': 16,
                }
                lidos = 0
                importados = 0
                atualizados = 0
                erros = 0
                for record in csv.reader(form.cleaned_data['arquivo'].read().split('\n')[1:], delimiter=',', quotechar='"'):
                    if len(record) >= 14:
                        lidos += 1
                        try:
                            uf = UF.objects.get(uf=record[var['uf']])
                            municipio = Municipio.objects.get(uf=uf, nome=record[var['municipio']])

                        except UF.DoesNotExist:
                            messages.error(request, u'Estado(%s) do colaborador %s não encontrado.' % (record[var['uf']], record[var['email']]))
                            uf = None

                        except Municipio.DoesNotExist:
                            municipio = None
                            uf = None

                        if not uf:
                            uf = UF.objects.get(uf='SP')

                        try:
                            # Atualiza o Membro
                            membro = Membro.objects.get(email=record[var['email']])
                            if not membro.nome:
                                membro.nome = record[var['nome']]
                            if not membro.uf:
                                membro.uf = uf
                            if municipio and not membro.municipio:
                                membro.municipio = municipio
                            membro.save()
                            atualizados += 1
                        except Membro.DoesNotExist:
                            # atualiza data
                            print 'adicionando %s' % record[var['nome']]
                            dtcadastro = record[var['dtcadastro']].split(' ')[0]
                            dtcadastro = datetime.strptime(dtcadastro, '%m/%d/%Y')
                            # Importa o Membro
                            membro = Membro(
                                email=record[var['email']],
                                nome=record[var['nome']],
                                uf=uf,
                                municipio=municipio,
                                municipio_eleitoral = record[var['municipio']],
                                dtcadastro=dtcadastro,
                                status_email = 'N')
                            membro.celular = record[var['celular']]
                            membro.telefone = record[var['residencial']]
                            membro.atividade_profissional = record[var['atividade_profissional']]
                            membro.rg = record[var['rg']]
                            membro.titulo_eleitoral = record[var['titulo_eleitoral']]
                            membro.filiacao_partidaria = record[var['filiacao_partidaria']]

                            dtnascimento = record[var['dtnascimento']]
                            if dtnascimento:
                                try:
                                    membro.dtnascimento = datetime.strptime(dtnascimento, '%d/%m/%Y')
                                except:
                                    print record[var['dtnascimento']]
                            membro.save()
                            importados += 1
#'zona_secao_eleitoral': 12, 'municipio_eleitoral',
#'uf_eleitoral': 14, 'foi_filiacao_partidaria': 15, 'filiacao_partidaria'

                messages.info(request, u'Lidos: %s; Importados: %s; Atualizados: %s; Erros: %s.' % (lidos, importados, atualizados, erros))
                return HttpResponseRedirect(reverse('admin:cadastro_membro_changelist'))

        return render_to_response(template_name, {
            'title': u'Importar visitantes e colaboradores',
            'form': form,
        },context_instance=RequestContext(request))

    def get_urls(self):
        urls_originais = super(MembroAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^import/$', self.wrap(self.import_membros), name='cadastro_membros_import_membros'),
        )
        return urls_customizadas + urls_originais

    def get_buttons(self, request, object_id):
        buttons = super(MembroAdmin, self).get_buttons(request, object_id)
        if not object_id and request.user.is_superuser:
            buttons.append(PowerButton(url=reverse('admin:cadastro_membros_import_membros'), label=u'Importar visitantes e colaboradores'))
        return buttons


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
    search_fields = ('titulo',)
    list_display = ('titulo', 'tipo', 'uf', 'oficial',)
    list_filter = ('tipo','uf',)
    fieldsets_edicao = (
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
        if request.user.groups.filter(name=u'Cadastro').exists() or request.user.is_superuser:
            return self.fieldsets_edicao
        return self.fieldsets

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name=u'Cadastro').exists() or CirculoMembro.objects.filter(circulo=obj, membro__usuario=request.user, administrador=True).exists():
            return ()
        else:
            return flatten_fieldsets(self.get_fieldsets(request, obj))

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
        if request.user.is_superuser or request.user.groups.filter(name=u'Comissão').exists():
            self.inlines = [CirculoEventoCirculoInline, CirculoMembroCirculoInline, ]
        else:
            self.inlines = [CirculoEventoCirculoInline,]
        return [inline(self.model, self.admin_site) for inline in self.inlines]

class MunicipioAdmin(PowerModelAdmin):
    search_fields = ('nome',)
    list_display = ('uf', 'nome', )
    list_filter = ('uf',)
    list_per_page = 20

class LogEntryAdmin(PowerModelAdmin):
    search_fields = ('object_repr', 'change_message', 'user__username', )
    list_filter = ('action_time', 'content_type', 'action_flag',)
    list_display = ('action_time', 'user', 'content_type', 'tipo', 'object_repr', 'change_message', )
    fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'tipo', 'change_message', )
    readonly_fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'tipo', 'change_message', )
    multi_search = (
        ('q1', u'Repr. do Objeto', ['object_repr', ]),
        ('q2', u'Mensagem', ['change_message', ]),
        ('q3', u'User', ['user__username', ]),
    )
    def tipo(self, obj):
        if obj.is_addition():
            return u"1-Adicionado"
        elif obj.is_change():
            return u"2-Modificado"
        elif obj.is_deletion():
            return u"3-Deletado"

admin.site.register(Circulo, CirculoAdmin)
admin.site.register(CirculoEvento)
admin.site.register(Membro, MembroAdmin)
admin.site.register(Pessoa, PessoaAdmin)
admin.site.register(UF)
admin.site.register(Municipio, MunicipioAdmin)
admin.site.register(LogEntry, LogEntryAdmin)

