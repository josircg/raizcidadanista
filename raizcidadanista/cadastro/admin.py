# -*- coding:utf-8 -*-
from django.contrib import admin, messages
from django.contrib.admin.util import flatten_fieldsets
from django.forms.models import modelform_factory
from django.utils.encoding import force_unicode
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Template
from django.template.context import RequestContext, Context
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.utils import simplejson
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

from datetime import datetime
from functools import partial
import csv

from forms import MembroImport, MalaDiretaForm
from models import Membro, Circulo, CirculoMembro, CirculoEvento, Pessoa, Lista, ListaCadastro, Campanha

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

    def mala_direta(self, request, form_class=MalaDiretaForm, template_name='admin/cadastro/pessoa/mala-direta.html'):
        if request.method == 'POST':
            if request.POST.get('lista') and request.POST.get('pessoas_ids'):
                lista = get_object_or_404(Lista, pk=request.POST.get('lista'), validade__gte=datetime.now(), status__in=('A', 'P'))
                num = 0
                for pessoa in Pessoa.objects.filter(pk__in=request.POST.get('pessoas_ids').split(',')):
                    obj, created = ListaCadastro.objects.get_or_create(lista=lista, pessoa=pessoa)
                    if created:
                        num += 1
                messages.info(request, u'Número de pessoas inseridas na lista: %s' % num)
            else:
                messages.warning(request, u'Nenhuma pessoa foi cadastrada!')

        if request.is_ajax():
            form = form_class(request.GET)
            if form.is_valid():
                pessoas = Pessoa.objects.all()
                # Filtros
                if form.cleaned_data.get('uf'):
                    pessoas = pessoas.filter(uf=form.cleaned_data.get('uf'))
                if form.cleaned_data.get('tipo'):
                    if form.cleaned_data.get('tipo') == 'V':
                        pessoas = pessoas.filter(membro__isnull=True)
                    elif form.cleaned_data.get('tipo') == 'C':
                        pessoas = pessoas.filter(membro__isnull=False, membro__filiado=False)
                    elif form.cleaned_data.get('tipo') == 'F':
                        pessoas = pessoas.filter(membro__isnull=False, membro__filiado=True)

                # Emails
                emails_list = pessoas.values_list('email', flat=True)
                pessoas_ids = pessoas.values_list('pk', flat=True)

                # Paginação
                paginator = Paginator(emails_list, 150)
                pagina = request.GET.get('pagina')
                try:
                    emails = paginator.page(pagina)
                except (PageNotAnInteger, EmptyPage):
                    pagina = 1
                    emails = paginator.page(1)

                return HttpResponse(simplejson.dumps({
                    'pagina': pagina,
                    'total_paginas': paginator.num_pages,
                    'emails': ', '.join(list(emails)),
                    'pessoas_ids': ','.join([str(pessoa_id) for pessoa_id in pessoas_ids]),
                    'total': emails_list.count()
                }), mimetype='application/json')
        form = form_class()
        return render_to_response(template_name, {
            'title': u'Mala direta',
            'form': form,
            'listas': Lista.objects.filter(validade__gte=datetime.now(), status__in=('A', 'P')),
        },context_instance=RequestContext(request))

    def get_urls(self):
        urls_originais = super(PessoaAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^mala-direta/$', self.wrap(self.mala_direta), name='cadastro_pessoa_mala_direta'),
        )
        return urls_customizadas + urls_originais

    def get_buttons(self, request, object_id):
        buttons = super(PessoaAdmin, self).get_buttons(request, object_id)
        if not object_id:
            buttons.append(PowerButton(url=reverse('admin:cadastro_pessoa_mala_direta'), label=u'Mala direta'))
        return buttons
admin.site.register(Pessoa, PessoaAdmin)


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

                if Lista.objects.filter(nome=u'Colaboradores').exists():
                    ListaCadastro(
                        lista = Lista.objects.get(nome=u'Colaboradores'),
                        pessoa = rec,
                    ).save()
        self.message_user(request, 'Total de Membros aprovados: %d' % contador)
    aprovacao.short_description = u'Aprovação'

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        else:
            return ('dtcadastro', 'usuario', 'facebook_id', 'aprovador',)

    def import_membros(self, request, form_class=MembroImport, template_name='admin/cadastro/membro/import.html'):
        var = {
            'dtcadastro': 0, 'nome': 1, 'uf': 2, 'municipio': 3, 'email': 4, 'celular': 5, 'operadora_celular': 6, 'residencial': 7,
            'atividade_profissional': 8, 'dtnascimento': 9, 'rg': 10, 'titulo_zona_secao_eleitoral': 11, 'municipio_eleitoral': 12,
            'uf_eleitoral': 13, 'foi_filiacao_partidaria': 14, 'filiacao_partidaria': 15,
        }

        def _get_data(record, name):
            return force_unicode(record[var[name]].strip())

        if not request.user.is_superuser:
            raise PermissionDenied()

        form = form_class()
        if request.method == 'POST':
            form = form_class(request.POST, request.FILES)
            if form.is_valid():
                lidos = 0
                importados = 0
                atualizados = 0
                erros = 0
                aprovador = Membro.objects.get(pk=1).usuario

                for record in csv.reader(form.cleaned_data['arquivo'].read().split('\n')[1:], delimiter=',', quotechar='"'):
                    if len(record) >= 14:
                        lidos += 1

                        try:
                            uf = UF.objects.get(uf=_get_data(record, 'uf'))
                            municipio = Municipio.objects.get(uf=uf, nome=_get_data(record, 'municipio')).nome

                        except UF.DoesNotExist:
                            messages.error(request, u'Estado(%s) do colaborador %s não encontrado.' % (_get_data(record, 'uf'), _get_data(record, 'email')))
                            uf = None

                        except Municipio.DoesNotExist:
                            municipio = None

                        try:
                            uf_eleitoral = UF.objects.get(uf=_get_data(record, 'uf_eleitoral'))
                            municipio_eleitoral = _get_data(record, 'municipio_eleitoral')
                            reg = Municipio.objects.get(uf=uf_eleitoral, nome=municipio_eleitoral)
                            municipio_eleitoral = reg.nome

                        except UF.DoesNotExist:
                            messages.error(request, u'Estado eleitoral(%s) do colaborador %s não encontrado.' % (_get_data(record, 'uf_eleitoral'), _get_data(record, 'email')))
                            uf_eleitoral = None
                            municipio_eleitoral = None

                        except Municipio.DoesNotExist:
                            municipio_eleitoral = None

                        if not uf:
                            uf = UF.objects.get(uf='SP')

                        try:
                            # Atualiza o Membro
                            membro = Membro.objects.get(email=_get_data(record, 'email'))
                            if not membro.nome:
                                membro.nome = _get_data(record, 'nome')
                            atualizados += 1
                        except Membro.DoesNotExist:
                            # atualiza data
                            dtcadastro = _get_data(record, 'dtcadastro').split(' ')[0]
                            dtcadastro = datetime.strptime(dtcadastro, '%m/%d/%Y')
                            # Importa o Membro
                            membro = Membro(
                                email=_get_data(record, 'email'),
                                nome=_get_data(record, 'nome'),
                                uf=uf,
                                municipio=municipio,
                                dtcadastro=dtcadastro,
                                status_email = 'N')
                            importados += 1

                        if not membro.uf:
                            membro.uf = uf

                        if municipio:
                            if not membro.municipio or membro.municipio.isdigit():
                                membro.municipio = municipio

                        if not membro.celular:
                            membro.celular = _get_data(record, 'celular').split('/')[0].strip()[:14]

                        if not membro.residencial:
                            membro.residencial = _get_data(record, 'residencial').split('/')[0].strip()[:14]

                        if not membro.atividade_profissional:
                            membro.atividade_profissional = _get_data(record, 'atividade_profissional')

                        if not membro.rg:
                            membro.rg = _get_data(record, 'rg')

                        if not membro.uf_eleitoral:
                            membro.uf_eleitoral = uf_eleitoral
                            membro.municipio_eleitoral = municipio_eleitoral
                            membro.titulo_eleitoral = _get_data(record, 'titulo_zona_secao_eleitoral')
                            if len(membro.titulo_eleitoral.split('/')) > 1:
                                try:
                                    membro.zona_eleitoral = membro.titulo_eleitoral.split('/')[1].strip()[0:3]
                                    membro.secao_eleitoral = membro.titulo_eleitoral.split('/')[2].strip()[0:4]
                                    membro.titulo_eleitoral = membro.titulo_eleitoral.split('/')[0].strip()
                                except:
                                    print u'erro título %s' % membro.titulo_eleitoral

                            membro.filiacao_partidaria = _get_data(record, 'filiacao_partidaria')

                        if municipio_eleitoral and not membro.municipio_eleitoral:
                            membro.municipio_eleitoral = municipio_eleitoral

                        if membro.titulo_eleitoral:
                            membro.filiado = True

                        dtnascimento = _get_data(record, 'dtnascimento')
                        if dtnascimento:
                            if len(dtnascimento.split('/')[2]) == 2:
                                ano = '19%s' % dtnascimento.split('/')[2]
                                dtnascimento = '%s/%s/%s' % ( dtnascimento.split('/')[0],
                                    dtnascimento.split('/')[1], ano )

                            membro.dtnascimento = datetime.strptime(dtnascimento, '%d/%m/%Y')

                        if not membro.aprovador:
                            membro.aprovador = aprovador

                        membro.save()

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
            buttons.append(PowerButton(url=reverse('admin:cadastro_membros_import_membros'), label=u'Importar colaboradores'))
        return buttons
admin.site.register(Membro, MembroAdmin)


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
admin.site.register(Circulo, CirculoAdmin)


class MunicipioAdmin(PowerModelAdmin):
    search_fields = ('nome',)
    list_display = ('uf', 'nome', )
    list_filter = ('uf',)
    list_per_page = 20
admin.site.register(Municipio, MunicipioAdmin)


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
admin.site.register(LogEntry, LogEntryAdmin)


class ListaCadastroAdmin(PowerModelAdmin):
    list_display = ('lista', 'pessoa', 'dtinclusao')
    list_filter = ('lista', 'dtinclusao', )
    multi_search = (
        ('q1', u'Pessoa', ['pessoa__nome', 'pessoa__email',]),
    )
    raw_id_fields = ('lista', 'pessoa')
    fieldsets = [
        (None, {
            'fields': (
                'lista', 'pessoa',
            )
        }),
    ]
admin.site.register(ListaCadastro, ListaCadastroAdmin)


class ListaAdmin(PowerModelAdmin):
    list_display = ('nome', 'validade', 'status', )
    list_filter = ('validade', 'status', )
    multi_search = (
        ('q1', u'Nome', ['nome', ]),
    )
    readonly_fields = ('num_cadastros', )
    actions = ('inativar', )

    fieldsets = [
        (None, {
            'fields': (
               'nome', 'validade', 'num_cadastros', 'status', 'seo', 'analytics'
            )
        }),
    ]

    def inativar(self, request, queryset):
        count = queryset.count()
        queryset.update(status=u'I')
        messages.info(request, u'%s lista(s) inativada(s).' % count)
    inativar.short_description = u'Inativar'

    def get_buttons(self, request, object_id):
        buttons = super(ListaAdmin, self).get_buttons(request, object_id)
        if object_id:
            buttons.append(PowerButton(url="%s?lista__id__exact=%s" % (reverse('admin:cadastro_listacadastro_changelist'), object_id), label=u'Cadastros'))
        return buttons
admin.site.register(Lista, ListaAdmin)


class CampanhaAdmin(PowerModelAdmin):
    list_display = ('lista', 'dtenvio', 'assunto', 'qtde_envio', 'qtde_erros', 'qtde_views',)
    list_filter = ('dtenvio', )
    raw_id_fields = ('lista', )
    multi_search = (
        ('q1', u'Assunto', ['assunto', ]),
        ('q2', u'Lista', ['lista__nome', ]),
    )
    fieldsets = [
        (None, { 'fields': ('lista', 'assunto', 'template', 'template_html', ), },),
    ]
    fieldsets_readonly = [
        (None, { 'fields': ('lista', 'assunto', ('qtde_envio', 'qtde_erros', 'qtde_views',), 'dtenvio', 'template', 'template_html',), },),
    ]
    readonly_fields = ('template_html', )

    def get_fieldsets(self, request, obj=None):
        if obj and obj.dtenvio:
            return self.fieldsets_readonly
        return self.fieldsets

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.dtenvio:
            return ('lista', 'qtde_envio', 'dtenvio', 'qtde_erros', 'qtde_views', 'template_html', )
        return ('template_html', )

    def teste_de_envio(self, request, id_campanha):
        campanha = get_object_or_404(Campanha, pk=id_campanha)
        if request.method == 'POST' and request.POST.get('email'):
            email = request.POST.get('email')
            campanha.send_email_test(to=[email, ])
            messages.info(request, u'O email enviado com sucesso!')
        else:
            messages.error(request, u'Preencha corretamento o campo email na hora de testar o envio.')
        return HttpResponseRedirect(reverse('admin:cadastro_campanha_change', args=(id_campanha, )))

    def envio(self, request, id_campanha):
        campanha = get_object_or_404(Campanha, pk=id_campanha)
        campanha.send_emails(request.user, resumir=False)
        messages.info(request, u'Os emails estão sendo enviados!')
        return HttpResponseRedirect(reverse('admin:cadastro_campanha_change', args=(id_campanha, )))

    def resumir_envio(self, request, id_campanha):
        campanha = get_object_or_404(Campanha, pk=id_campanha)
        campanha.send_emails(request.user, resumir=True)
        messages.info(request, u'Os emails estão sendo enviados!')
        return HttpResponseRedirect(reverse('admin:cadastro_campanha_change', args=(id_campanha, )))

    def template(self, request, id_campanha):
        campanha = get_object_or_404(Campanha, pk=id_campanha)
        template_content = Template(campanha.template)
        html_content = template_content.render(Context({}))
        return HttpResponse(html_content)

    def copiar(self, request, id_campanha):
        campanha = get_object_or_404(Campanha, pk=id_campanha)
        nova_campanha = Campanha.objects.create(
            assunto = campanha.assunto,
            template = campanha.template,
        )
        messages.info(request, u'Cópia da campanha %s criada com sucesso!' % campanha)
        return HttpResponseRedirect(reverse('admin:cadastro_campanha_change', args=(nova_campanha.pk, )))

    def get_urls(self):
        urls_originais = super(CampanhaAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^(?P<id_campanha>\d+)/teste-de-envio/$', self.wrap(self.teste_de_envio), name='cadastro_campanha_teste_de_envio'),
            url(r'^(?P<id_campanha>\d+)/envio/$', self.wrap(self.envio), name='cadastro_campanha_envio'),
            url(r'^(?P<id_campanha>\d+)/resumir-envio/$', self.wrap(self.resumir_envio), name='cadastro_campanha_resumir_envio'),
            url(r'^(?P<id_campanha>\d+)/template/$', self.wrap(self.template), name='cadastro_campanha_template'),
            url(r'^(?P<id_campanha>\d+)/copiar/$', self.wrap(self.copiar), name='cadastro_campanha_copiar'),
        )
        return urls_customizadas + urls_originais

    def get_buttons(self, request, object_id):
        buttons = super(CampanhaAdmin, self).get_buttons(request, object_id)
        obj = self.get_object(request, object_id)
        if obj:
            buttons.append(PowerButton(url='?lightbox[width]=280&lightbox[height]=90#box-teste_de_envio', attrs={'class': 'historylink lightbox', }, label=u'Teste de Envio'))
            if not obj.dtenvio:
                buttons.append(PowerButton(url=reverse('admin:cadastro_campanha_envio', kwargs={'id_campanha': object_id, }), label=u'Envio'))
            if obj.qtde_erros > 0:
                buttons.append(PowerButton(url=reverse('admin:cadastro_campanha_resumir_envio', kwargs={'id_campanha': object_id, }), label=u'Resumir envio interrompido'))
            buttons.append(PowerButton(url=reverse('admin:cadastro_campanha_copiar', kwargs={'id_campanha': object_id, }), label=u'Copiar'))
        return buttons
admin.site.register(Campanha, CampanhaAdmin)



admin.site.register(CirculoEvento)
admin.site.register(UF)
