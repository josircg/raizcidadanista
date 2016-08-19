# -*- coding:utf-8 -*-
from django.contrib import admin, messages
from django.contrib.admin.util import flatten_fieldsets
from django.forms.models import modelform_factory
from django.utils.encoding import force_unicode
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Template
from django.template.loader import get_template
from django.template.context import RequestContext, Context
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
from django.utils import simplejson
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.defaultfilters import date as _date
from django.db.models import Sum, Q

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from decimal import Decimal
from datetime import datetime, date, timedelta
from functools import partial
import os
import csv
import requests
from bs4 import BeautifulSoup

import cStringIO as StringIO
import cgi
from xhtml2pdf.pisa import pisaDocument
from ckeditor.widgets import CKEditorWidget

from forms import MembroImport, MalaDiretaForm, ArticleCadastroForm, InclusaoEmLoteForm
from models import Membro, Filiado, Circulo, CirculoMembro, CirculoEvento, Pessoa, Lista, ListaCadastro, Campanha, \
    ColetaArticulacao, ArticleCadastro, Candidatura, Coligacao
from financeiro.models import Receita

from forum.models import Grupo, GrupoUsuario
from municipios.models import UF, Municipio
from cms.models import Section, URLMigrate, SectionItem
from cms.email import sendmail
from poweradmin.admin import PowerModelAdmin, PowerButton


class PessoaAdmin(PowerModelAdmin):
    list_display = ('nome', 'email', 'status_email', 'uf', 'municipio', 'dtcadastro',)
    search_fields = ('nome', 'email',)
    list_filter = ('uf', 'dtcadastro')
    actions = ('validar_email', )

    def validar_email(self, request, queryset):
        contador = 0
        for rec in queryset:
            if rec.status_email == 'N':
                contador += 1
                sendmail(
                    subject=u'RAiZ Movimento Cidadanista - Validação de email',
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
                if form.cleaned_data.get('grupo'):
                    pessoas = pessoas.filter(membro__usuario__groups=form.cleaned_data.get('grupo'))
                if form.cleaned_data.get('uf'):
                    pessoas = pessoas.filter(uf=form.cleaned_data.get('uf'))
                if form.cleaned_data.get('tipo'):
                    if form.cleaned_data.get('tipo') == 'C':
                        pessoas = pessoas.filter(membro__isnull=False, membro__filiado=False)
                    elif form.cleaned_data.get('tipo') == 'F':
                        pessoas = pessoas.filter(membro__isnull=False, membro__filiado=True)
                if form.cleaned_data.get('circulo'):
                    pessoas = pessoas.filter(membro__circulomembro__circulo=form.cleaned_data.get('circulo'))

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

    def inclusao_em_lote(self, request, form_class=InclusaoEmLoteForm, template_name='admin/cadastro/pessoa/inclusao-em-lote.html'):
        var = {'email': 0, 'nome': 1, 'telefone': 2, 'uf': 3, 'circulo': 4}

        def _get_data(record, name):
            if name in var:
                return force_unicode(record[var[name]].strip())
            else:
                return None

        if not request.user.is_superuser:
            raise PermissionDenied()

        form = form_class()
        num_lidos = importados = atualizados = num_circulo = 0
        visitantes = []
        if request.method == 'POST':
            form = form_class(request.POST, request.FILES)
            if form.is_valid():
                for record in csv.reader(form.cleaned_data['arquivo'].read().split('\n')[1:], delimiter=',', quotechar='"'):

                    if len(record) >= 2:
                        num_lidos += 1
                        email = _get_data(record, 'email')
                    else:
                        email = None

                    # Se tem email
                    if email:
                        # Pega o UF
                        uf = _get_data(record, 'uf')
                        if uf:
                            try: uf = UF.objects.get(uf=uf)
                            except UF.DoesNotExist: pass

                        # Se for membro, então verifica se é para adicionar no círculo
                        if Membro.objects.filter(email=email).exists():
                            if _get_data(record, 'circulo'):
                                circulo = Circulo.objects.filter(id=_get_data(record, 'circulo'))
                                if circulo.count() == 1:
                                    membro = Membro.objects.get(email=email)
                                    circulo, insert = CirculoMembro.objects.get_or_create(membro=membro,circulo=circulo[0])
                                    if insert:
                                        num_circulo += 1

                        else:
                            # Se não for membro, então tenta encontrar a pessoa
                            if Pessoa.objects.filter(email=email).exists():
                                for pessoa in Pessoa.objects.filter(email=email):
                                    # Inclui na lista de visitantes
                                    visitantes.append(pessoa)
                                    atualizado = False
                                    # Atualizar nome e telefone
                                    if _get_data(record, 'nome') and pessoa.nome != _get_data(record, 'nome'):
                                        pessoa.nome = _get_data(record, 'nome')
                                        atualizado = True
                                    if _get_data(record, 'telefone') and pessoa.celular != None:
                                        pessoa.celular = _get_data(record, 'telefone').strip(' ')[0:13]
                                        atualizado = True
                                    if pessoa.uf == None and uf:
                                        pessoa.uf = uf
                                        atualizado = True

                                    if atualizado:
                                        pessoa.save()
                                        atualizados += 1
                            # Cria a pessoa
                            else:
                                if _get_data(record, 'nome') and uf:
                                    pessoa = Pessoa(
                                        email=email,
                                        nome=_get_data(record, 'nome'),
                                        celular=_get_data(record, 'telefone').strip(' ')[0:13],
                                        uf=uf,
                                    )
                                    pessoa.save()
                                    visitantes.append(pessoa)
                                    importados += 1
                messages.info(request, u'Registros lidos: %s | Importados: %s | Atualizados: %s | Novos membros no círculo: %s' % (num_lidos, importados, atualizados, num_circulo))
        return render_to_response(template_name, {
            'title': u'Inclusão em lote',
            'form': form,
            'visitantes': visitantes,
        },context_instance=RequestContext(request))

    def get_urls(self):
        urls_originais = super(PessoaAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^mala-direta/$', self.wrap(self.mala_direta), name='cadastro_pessoa_mala_direta'),
            url(r'^inclusao-em-lote/$', self.wrap(self.inclusao_em_lote), name='cadastro_pessoa_inclusao_em_lote'),
        )
        return urls_customizadas + urls_originais

    def get_buttons(self, request, object_id):
        buttons = super(PessoaAdmin, self).get_buttons(request, object_id)
        obj = self.get_object(request, object_id)
        if obj:
            if Membro.objects.filter(pessoa_ptr=obj).exists():
                buttons.append(PowerButton(url=reverse('admin:cadastro_membro_change', args=(obj.membro.pk, )), label=u'Colaborador'))
        else:
            buttons.append(PowerButton(url=reverse('admin:cadastro_pessoa_mala_direta'), label=u'Mala direta'))
            buttons.append(PowerButton(url=reverse('admin:cadastro_pessoa_inclusao_em_lote'), label=u'Inclusão em Lote'))
        return buttons
admin.site.register(Pessoa, PessoaAdmin)


class CirculoMembroMembroInline(admin.TabularInline):
    model = CirculoMembro
    extra = 1
    verbose_name = u'Círculo do Membro'
    verbose_name_plural = u'Círculos do Membro'
    raw_id_fields = ('membro', )

    def has_add_permission(self, request):
        if not request.user.is_superuser:
            return False
        return super(CirculoMembroMembroInline, self).has_add_permission(request)


class MembroAdmin(PowerModelAdmin):
    list_display = ('nome', 'email', 'rg', 'uf', 'municipio_eleitoral', 'dtcadastro', 'aprovador', )
    list_filter = ('uf', 'uf_eleitoral', 'fundador', 'assinado', 'filiado', 'status_email', )
    search_fields = ('nome', 'email',)
    multi_search = (
        ('q1', u'Nome', ['nome', ]),
        ('q2', u'E-mail', ['email', ]),
        ('q3', u'Profissão', ['atividade_profissional', ]),
    )
    inlines = (CirculoMembroMembroInline, )
    actions = ('aprovacao', 'estimativa_de_recebimento', 'colaboradores_sem_pagamento_csv', 'lista_colaboradores_sem_pagamento', 'atualizacao_cadastral', 'requerimento', 'requerimento_html', 'listagem_telefonica', 'assinatura', )

    fieldsets = (
        (None, {
            'fields': ['nome', 'apelido', 'email', ('sexo', 'estadocivil', 'dtnascimento'), 'atividade_profissional',  'rg', 'cpf', ('celular', 'residencial'), ('uf_naturalidade', 'municipio_naturalidade'), ]
        }),
        ('Situação Cadastral', {
            'fields': [ ('status_email', 'usuario', 'aprovador'), ('filiado', 'fundador', 'assinado'), ('dt_prefiliacao', 'dtcadastro'), ]
        }),
        (u'Dados eleitorais', {
            'fields': ['nome_da_mae', 'uf_eleitoral', 'municipio_eleitoral', ('titulo_eleitoral', 'zona_eleitoral', 'secao_eleitoral'), 'filiacao_partidaria', ]
        }),
        (u'Endereço', {
            'fields': [('endereco_cep', 'uf', 'municipio'), ('endereco', 'endereco_num', 'endereco_complemento'), ]
        }),
        (u'Contribuição', {
            'fields': ['contrib_tipo', 'contrib_valor', 'contrib_prox_pgto', ]
        }),
    )

    def get_actions(self, request):
        allactions = super(MembroAdmin, self).get_actions(request)
        if request.user.is_superuser:
            return allactions
        actions = {}
        if request.user.groups.filter(name=u'Coordenador Local').exists():
            if allactions.get('listagem_telefonica'):
                actions['listagem_telefonica'] = allactions['listagem_telefonica']

        if request.user.groups.filter(name=u'Comissao').exists():
            for action in ('aprovacao', 'atualizacao_cadastral', 'requerimento', 'requerimento_html', 'assinatura', ):
                if allactions.get(action):
                    actions[action] = allactions[action]

        if request.user.groups.filter(name=u'Financeiro').exists():
            for action in ('estimativa_de_recebimento', 'colaboradores_sem_pagamento_csv', 'lista_colaboradores_sem_pagamento', 'atualizacao_cadastral', 'requerimento', 'requerimento_html', 'assinatura', 'delete_selected', 'export_as_csv', ):
                if allactions.get(action):
                    actions[action] = allactions[action]
        return actions

    def get_list_display_links(self, request, list_display):
        if not request.user.groups.filter(name=u'Comissao').exists() and not request.user.is_superuser:
            return []
        return super(MembroAdmin, self).get_list_display_links(request, list_display)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.groups.filter(name=u'Comissao').exists() and not request.user.is_superuser:
            return False
        return super(MembroAdmin, self).has_change_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('usuario', 'aprovador',)
        else:
            return ('dtcadastro', 'usuario', 'facebook_id', 'aprovador', 'twitter_id')


    def aprovacao(self, request, queryset):
        contador = 0
        if not Campanha.objects.filter(assunto__icontains="[Boas Vindas]"):
            self.message_user(request, 'Template [Boas Vindas] não encontrado')

        for rec in queryset:
            if rec.aprovador is None:
                if not rec.status_email in ('S', 'O'):
                    # Buscar o template de "[Boas Vindas]" nas Campanhas
                    template = Campanha.objects.filter(assunto__icontains="[Boas Vindas]").latest('pk')
                    sendmail(
                            subject=u'Seja bemvindx à RAiZ Movimento Cidadanista',
                            to=[rec.email, ],
                            template=template.template,
                            params={},
                    )
                    contador += 1
                    rec.aprovador = request.user
                    rec.save()

                if Lista.objects.filter(nome=u'Colaboradores').exists():
                    ListaCadastro(
                        lista = Lista.objects.get(nome=u'Colaboradores'),
                        pessoa = rec,
                    ).save()

        self.message_user(request, 'Total de Membros aprovados: %d' % contador)
    aprovacao.short_description = u'Aprovação'

    def estimativa_de_recebimento(self, request, queryset, template_name_pdf='admin/cadastro/membro/estimativa-de-recebimento-pdf.html'):
        hoje = date.today()
        total = Decimal(0.0)
        results = []
        for query in queryset:
            vr_apagar = query.vr_apagar(hoje)
            if vr_apagar > Decimal(0.0):
                total += vr_apagar
                results.append({
                    'membro': query,
                    'vr_apagar': vr_apagar,
                })

        template = get_template(template_name_pdf)
        context = RequestContext(request, {
            'title': u'Estimativa de Recebimento - %s' % hoje.strftime("%B %Y"),
            'results': results,
            'total': total,
        })
        html  = template.render(context)

        dataresult = StringIO.StringIO()
        pdf = pisaDocument(StringIO.StringIO(html.encode("UTF-8")), dest=dataresult)
        if not pdf.err:
            return HttpResponse(dataresult.getvalue(), mimetype='application/pdf')
        return HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))
    estimativa_de_recebimento.short_description = u'Estimativa de Recebimento'

    # TODO: Desativado #66
    def colaboradores_sem_pagamento(self, request, queryset, template_name_pdf='admin/cadastro/membro/colaboradores-sem-pagamento-pdf.html'):
        colaboradores_com_pagamento_ids = Receita.objects.filter(colaborador__in=queryset).values_list('colaborador', flat=True)
        results = queryset.exclude(pk__in=colaboradores_com_pagamento_ids).filter(Q(filiado=True) | Q(contrib_valor__gt=0)).distinct()

        template = get_template(template_name_pdf)
        context = RequestContext(request, {
            'title': u'Colaboradores sem pagamento - Raiz Cidadanista',
            'results': results,
            'total': results.aggregate(total=Sum('contrib_valor')).get('total', 0)
        })
        html  = template.render(context)

        dataresult = StringIO.StringIO()
        pdf = pisaDocument(StringIO.StringIO(html.encode("UTF-8")), dest=dataresult)
        if not pdf.err:
            return HttpResponse(dataresult.getvalue(), mimetype='application/pdf')
        return HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))
    colaboradores_sem_pagamento.short_description = u'Colaboradores sem pagamento'

    def colaboradores_sem_pagamento_csv(self, request, queryset):
        colaboradores_com_pagamento_ids = Receita.objects.filter(colaborador__in=queryset).values_list('colaborador', flat=True)
        results = queryset.exclude(pk__in=colaboradores_com_pagamento_ids).filter(Q(filiado=True) | Q(contrib_valor__gt=0)).distinct()
        csv = u'"Nome";"Email";"Contribuição";"Valor"\n'
        for colaborador in results:
            csv += u'"%(nome)s";"%(email)s";"%(contrib_tipo)s";"%(contrib_valor)s"\n' % {
                'nome': u'%s' % colaborador.membro.nome,
                'email': colaborador.membro.email,
                'contrib_tipo': colaborador.get_contrib_tipo_display(),
                'contrib_valor': colaborador.contrib_valor,
            }
        response = HttpResponse(csv, mimetype='application/csv; charset=utf-8', )
        response['Content-Disposition'] = 'filename=Colaboradores_sem_pagamento.csv'
        return response
    colaboradores_sem_pagamento_csv.short_description = u'Colaboradores sem pagamento - csv'

    def lista_colaboradores_sem_pagamento(self, request, queryset):
        colaboradores_com_pagamento_ids = Receita.objects.filter(colaborador__in=queryset).values_list('colaborador', flat=True)
        results = queryset.exclude(pk__in=colaboradores_com_pagamento_ids).filter(Q(filiado=True) | Q(contrib_valor__gt=0)).distinct()

        lista = Lista(nome=u'Colaboradores sem pagamento', validade=datetime.now(), status='P')
        lista.save()

        for colaborador in results:
            ListaCadastro(lista=lista, pessoa=colaborador).save()

        messages.info(request, u'Lista criada com sucesso!')
        return HttpResponseRedirect(reverse('admin:cadastro_lista_change', args=(lista.pk, )))
    lista_colaboradores_sem_pagamento.short_description = u'Lista Colaboradores sem pagamento'

    def atualizacao_cadastral(self, request, queryset):
        campanhas = Campanha.objects.filter(assunto__icontains=u'[!]').order_by('pk')
        if not campanhas.exists():
            messages.warning(request, u'Nenhuma campanha cadastrada para Atualização Cadastral.')
            return

        contador = 0
        for membro in queryset:
            if membro.status_email in ('S', 'O'):
                messages.warning(request, u'Membro %s está inativo ou em lista de SPAM' % membro.nome)
            else:
                sendmail(
                    subject=campanhas[0].assunto,
                    to=[membro.email, ],
                    template=campanhas[0].template,
                    params={
                        'link': u'%s%s' % (settings.SITE_HOST, membro.get_absolute_update_url()),
                    },
                )
                contador += 1

        self.message_user(request, 'Total de Emails enviados: %d' % contador)
    atualizacao_cadastral.short_description = u'Atualização Cadastral'

    def requerimento(self, request, queryset, template_name_pdf='admin/cadastro/membro/requerimento-pdf.html'):
        results = {}
        for estado in set(queryset.values_list('uf_eleitoral__nome', flat=True)):
            results[estado] = queryset.filter(uf_eleitoral__nome=estado)

        template = get_template(template_name_pdf)
        context = RequestContext(request, {
            'results': results,
        })
        html  = template.render(context)

        dataresult = StringIO.StringIO()
        pdf = pisaDocument(StringIO.StringIO(html.encode("UTF-8")), dest=dataresult)
        if not pdf.err:
            return HttpResponse(dataresult.getvalue(), mimetype='application/pdf')
        return HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))
    requerimento.short_description = u'Requerimento'

    def requerimento_html(self, request, queryset, template_name='admin/cadastro/membro/requerimento-html.html'):
        results = []
        estados = UF.objects.filter(pk__in=queryset.values_list('uf_eleitoral', flat=True)).order_by('nome').distinct()
        index = 1
        erros = []
        for estado in estados:
            membros = []
            for membro in queryset.filter(uf_eleitoral=estado).order_by('nome'):
                membro.index = index
                index += 1
                membros.append(membro)
#                if not membro.celular:
#                    erros.append( u'Membro %s sem telefone' % membro.nome )

                if membro.uf is None or membro.uf != membro.uf_eleitoral:
                    erros.append( u'Membro %s com UF diferente' % membro.nome )

                if not membro.municipio:
                    erros.append( u'Membro %s sem cidade no endereço' % membro.nome )

                if not membro.uf_naturalidade:
                    erros.append( u'Membro %s sem UF na naturalidade' % membro.nome )

            results.append([estado, membros])

        return render_to_response(template_name, {
            'results': results,
            'erros': erros,
        },context_instance=RequestContext(request))
    requerimento_html.short_description = u'Requerimento em Texto'

    def listagem_telefonica(self, request, queryset, template_name_pdf='admin/cadastro/membro/listagem-telefonica-pdf.html'):
        template = get_template(template_name_pdf)
        context = RequestContext(request, {
            'results': queryset,
        })
        html  = template.render(context)

        dataresult = StringIO.StringIO()
        pdf = pisaDocument(StringIO.StringIO(html.encode("UTF-8")), dest=dataresult)
        if not pdf.err:
            return HttpResponse(dataresult.getvalue(), mimetype='application/pdf')
        return HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))
    listagem_telefonica.short_description = u'Listagem Telefônica'

    def assinatura(self, request, queryset):
        contador = 0
        for rec in queryset:
            if rec.fundador:
                rec.assinado = True
                rec.save()
                contador += 1
        self.message_user(request, 'Total de Assinaturas marcadas: %d' % contador)
    assinatura.short_description = u'Assinatura realizada'

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
                            municipio = None
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
                            print u'municipio Eleitoral não encontrado %s:%s:' % (uf_eleitoral,municipio_eleitoral)
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

                    # Visitantes
                    if len(record) == 7:
                        lidos += 1
                        try:
                            uf = UF.objects.get(uf=_get_data(record, 'uf'))
                            municipio = Municipio.objects.get(uf=uf, nome=_get_data(record, 'municipio')).nome

                        except UF.DoesNotExist:
                            messages.error(request, u'Estado(%s) de %s não encontrado.' % (_get_data(record, 'uf'), _get_data(record, 'email')))
                            uf = None
                            municipio = None

                        except Municipio.DoesNotExist:
                            municipio = None

                        if not uf:
                            uf = UF.objects.get(uf='SP')

                        # obtem data de cadastro
                        try:
                            dtcadastro = _get_data(record, 'dtcadastro').split(' ')[0]
                            dtcadastro = datetime.strptime(dtcadastro, '%m/%d/%Y')
                        except:
                            try:
                                dtcadastro = datetime.strptime(dtcadastro, '%m/%d/%y')
                            except:
                                dtcadastro = None

                        try:
                            # Verifica se o visitante existe
                            pessoa = Pessoa.objects.get(email=_get_data(record, 'email'))
                            atualizados += 1
                        except Pessoa.DoesNotExist:
                            # Importa o Visitante
                            pessoa = Pessoa(
                                email=_get_data(record, 'email'),
                                nome=_get_data(record, 'nome'),
                                uf=uf,
                                municipio=municipio,
                                dtcadastro=dtcadastro,
                                status_email = 'N')
                            pessoa.save()

                            LogEntry.objects.log_action(
                                user_id = aprovador.pk,
                                content_type_id = ContentType.objects.get_for_model(pessoa).pk,
                                object_id = pessoa.pk,
                                object_repr = u'%s' % pessoa,
                                action_flag = ADDITION,
                                change_message = u'Importado do Google Drive')

                            importados += 1

                        if not pessoa.uf:
                            pessoa.uf = uf

                        if municipio:
                            if not pessoa.municipio:
                                pessoa.municipio = municipio

                        if not pessoa.celular:
                            pessoa.celular = _get_data(record, 'celular').split('/')[0].strip()[:14]

                        if not pessoa.residencial:
                            pessoa.residencial = _get_data(record, 'residencial').split('/')[0].strip()[:14]

                        pessoa.save()


                messages.info(request, u'Lidos: %s; Importados: %s; Atualizados: %s; Erros: %s.' % (lidos, importados, atualizados, erros))
                return HttpResponseRedirect(reverse('admin:cadastro_membro_changelist'))

        return render_to_response(template_name, {
            'title': u'Importar visitantes e colaboradores',
            'form': form,
        },context_instance=RequestContext(request))


    def antecedesntes_politicos(self, request, object_id, template_name='admin/cadastro/membro/antecedesntes_politicos.html'):
        object = self.get_object(request, object_id)
        if not object:
            raise Http404
        cpf = object.cpf
        if cpf:
            cpf = cpf.replace('.', '').replace('-', '')
        json = requests.get(u'http://politicos.olhoneles.org/api/v0/politicians/?candidacies__politician__cpf=%s' % cpf).json()
        candidaturas = []
        for obj in json.get('objects'):
            for cand in obj.get('candidacies'):
                candidaturas.append({
                    'data': datetime.strptime(cand.get('election_round').get('date', ''), '%Y-%m-%d') if cand.get('election_round') else '',
                    'cargo': cand.get('political_office').get('name', '') if cand.get('political_office') else '',
                    'cidade': cand.get('city').get('name', '') if cand.get('city') else '',
                    'estado': cand.get('state').get('name', '') if cand.get('state') else '',
                    'eleito': cand.get('elected', ''),
                })
        return render_to_response(template_name, {
            'object': object,
            'candidaturas': candidaturas,
            'title': u'Antecedentes Políticos',
        },context_instance=RequestContext(request))

    def get_urls(self):
        urls_originais = super(MembroAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^import/$', self.wrap(self.import_membros), name='cadastro_membros_import_membros'),
            url(r'^(?P<object_id>\d+)/antecedesntes_politicos/$', self.wrap(self.antecedesntes_politicos), name='cadastro_membros_antecedesntes_politicos'),
        )
        return urls_customizadas + urls_originais

    def get_buttons(self, request, object_id):
        buttons = super(MembroAdmin, self).get_buttons(request, object_id)
        obj = self.get_object(request, object_id)
        if obj:
            buttons.append(PowerButton(url=u'http://www.tse.jus.br/eleitor/servicos/titulo-e-local-de-votacao/consulta-por-nome', label=u'TSE'))
            buttons.append(PowerButton(url=reverse('admin:cadastro_membros_antecedesntes_politicos', kwargs={'object_id': object_id,}), label=u'Antecedentes Políticos'))
            if obj.receita_set.all().exists():
                buttons.append(PowerButton(url=u'%s?q2=%s&o=-5' % (reverse('admin:financeiro_receita_changelist'), obj.nome ,), label=u'Pagamentos'))

        if not obj and request.user.is_superuser:
            buttons.append(PowerButton(url=reverse('admin:cadastro_membros_import_membros'), label=u'Importar colaboradores'))
        return buttons

    def queryset(self, request):
        qs = super(MembroAdmin, self).queryset(request)
        if request.user.is_superuser or request.user.groups.filter(name__in=('Comissão', 'Cadastro')).exists():
            return qs
        if request.user.groups.filter(name=u'Coordenador Local').exists():
            uf_administrador_ids = CirculoMembro.objects.filter(membro__usuario=request.user, administrador=True).values_list('circulo__uf', flat=True)
            qs = qs.filter(uf__pk__in=uf_administrador_ids)
        if request.user.groups.filter(name=u'Articulador').exists():
            uf_ids = ColetaArticulacao.objects.filter(articulador__usuario=request.user).values_list('UF', flat=True)
            qs = qs.filter(uf__pk__in=uf_ids)
        return qs
admin.site.register(Membro, MembroAdmin)


class FiliadoAdmin(PowerModelAdmin):
    list_display = ('nome', 'email', 'municipio', 'dtcadastro', 'dt_prefiliacao', 'contrib_tipo', 'contrib_valor')
    list_filter = ('uf', 'contrib_tipo', 'fundador', )
    search_fields = ('nome', 'email',)
    inlines = (CirculoMembroMembroInline, )

    fieldsets = (
        (None, {
            'fields': ['nome', 'apelido', 'email', 'sexo', 'estadocivil',  'atividade_profissional', 'dtnascimento', 'rg', 'cpf', 'celular', 'residencial', 'uf_naturalidade', 'municipio_naturalidade', ]
        }),
        (None, {
            'fields': ['dtcadastro', 'status_email', 'usuario', 'aprovador', 'filiado', 'dt_prefiliacao', 'fundador', ]
        }),
        (u'Dados eleitorais', {
            'fields': ['nome_da_mae', 'uf_eleitoral', 'municipio_eleitoral', 'titulo_eleitoral', 'zona_eleitoral', 'secao_eleitoral', 'filiacao_partidaria', ]
        }),
        (u'Endereço', {
            'fields': [('endereco_cep', 'uf', 'municipio', ), 'endereco', 'endereco_num', 'endereco_complemento', ]
        }),
        (u'Contribuição', {
            'fields': ['contrib_tipo', 'contrib_valor', 'contrib_prox_pgto', ]
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        else:
            return ('dtcadastro', 'usuario', 'facebook_id', 'aprovador','twitter_id')

    def queryset(self, request):
        qs = super(FiliadoAdmin, self).queryset(request).filter(filiado=True)
        if request.user.groups.filter(name=u'Articulador').exists():
            uf_ids = ColetaArticulacao.objects.filter(articulador__usuario=request.user).values_list('UF', flat=True)
            qs = qs.filter(uf__pk__in=uf_ids)
        return qs

admin.site.register(Filiado, FiliadoAdmin)


class CirculoMembroCirculoInline(admin.TabularInline):
    model = CirculoMembro
    extra = max_num = 0
    verbose_name = u'Membro do Círculo'
    verbose_name_plural = u'Membros do Círculo'
    raw_id_fields = ('membro', )
    ordering = ('membro__nome', )
    fields = ('membro', 'email', 'celular', 'residencial', 'is_filiado', 'administrador', 'publico', )
    readonly_fields = ('membro', 'email', 'celular', 'residencial', 'is_filiado', )
    template = 'admin/cadastro/circulo/circulomembro_inline.html'

    def queryset(self, request):
        return super(CirculoMembroCirculoInline, self).queryset(request).exclude(membro__status_email='O')

    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super(CirculoMembroCirculoInline, self).get_formset(request, obj, **kwargs)
        class PaginationFormSet(FormSet):
            def _construct_forms(self, *args, **kwargs):
                qs = self.get_queryset()

                # Filtros
                if request.GET.get('nome'):
                    qs = qs.filter(membro__nome__icontains=request.GET.get('nome'))
                if request.GET.get('email'):
                    qs = qs.filter(membro__email__icontains=request.GET.get('email'))
                if request.GET.get('celular'):
                    qs = qs.filter(membro__celular__icontains=request.GET.get('celular'))
                if request.GET.get('residencial'):
                    qs = qs.filter(membro__residencial__icontains=request.GET.get('residencial'))
                if request.GET.get('filiado'):
                    qs = qs.filter(membro__filiado=True if request.GET.get('filiado') else False)
                if request.GET.get('administrador'):
                    qs = qs.filter(administrador=True if request.GET.get('administrador') else False)
                if request.GET.get('publico'):
                    qs = qs.filter(publico=True if request.GET.get('publico') else False)

                paginator = Paginator(qs, 20)

                try:
                    page_num = int(request.GET.get('page', '1'))
                except ValueError:
                    page_num = 1

                try:
                    page = paginator.page(page_num)
                except (EmptyPage, InvalidPage):
                    page = paginator.page(paginator.num_pages)

                self.paginator = paginator
                self.page = page
                self._queryset = page.object_list
                self.max_num = len(page.object_list)

                return super(PaginationFormSet, self)._construct_forms(*args, **kwargs)
        return PaginationFormSet

class CirculoMembroCirculoAddInline(admin.TabularInline):
    model = CirculoMembro
    extra = max_num = 1
    verbose_name = u'Adicionar Membro do Círculo'
    verbose_name_plural = u'Adicionar Membros do Círculo'
    raw_id_fields = ('membro', )
    fields = ('membro', 'administrador', 'publico', )

    def queryset(self, request):
        return super(CirculoMembroCirculoAddInline, self).queryset(request).none()

class CirculoEventoCirculoInline(admin.TabularInline):
    model = CirculoEvento
    extra = 0
    verbose_name = u'Evento do Círculo'
    verbose_name_plural = u'Eventos do Círculo'

    def actions(self, model):
        return u'<a href="%s">Enviar email</a>' % reverse('admin:cadastro_circulo_enviar_convite_evento', kwargs={'id_evento': model.pk})
    actions.allow_tags = True
    actions.short_description = u'Ações'

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or CirculoMembro.objects.filter(circulo=obj, membro__usuario=request.user, administrador=True).exists() or request.user.groups.filter(name=u'Comissão').exists():
            self.max_num = None
            return ('actions', )
        self.max_num = 0
        return ('nome', 'dt_evento', 'local', 'actions')

class CirculoAdmin(PowerModelAdmin):
    search_fields = ('titulo',)
    list_display = ('titulo', 'tipo', 'permitecadastro', 'uf', 'oficial', 'num_membros', 'status',)
    list_filter = ('tipo', 'uf', 'status', )
    fieldsets_edicao = (
        (None, {"fields" : ('titulo', 'slug', 'descricao', ('tipo', 'oficial',), ('uf', 'municipio', ), 'permitecadastro', 'dtcadastro', 'site_externo', 'imagem', 'status', 'num_membros', ),},),
    )
    fieldsets = (
        (None, {"fields" : ('titulo', 'slug', 'descricao', 'permitecadastro', ('uf', 'municipio', ), 'site_externo', 'imagem', 'dtcadastro', 'status'),}, ),
    )
    readonly_fields = ('num_membros', )
    actions = ('export_csv', 'criar_forum')

    def get_inline_instances(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name=u'Cadastro').exists():
            self.inlines = [CirculoEventoCirculoInline, CirculoMembroCirculoInline, CirculoMembroCirculoAddInline, ]
        else:
            self.inlines = [CirculoEventoCirculoInline, CirculoMembroCirculoInline, ]
        return [inline(self.model, self.admin_site) for inline in self.inlines]

    def get_actions(self, request):
        actions = super(CirculoAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
        return actions

    def get_fieldsets(self, request, obj=None):
        if request.user.groups.filter(name=u'Cadastro').exists() or request.user.is_superuser:
            return self.fieldsets_edicao
        return self.fieldsets

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name=u'Cadastro').exists() or CirculoMembro.objects.filter(circulo=obj, membro__usuario=request.user, administrador=True).exists():
            return self.readonly_fields
        else:
            return flatten_fieldsets(self.get_fieldsets(request, obj))

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

    def criar_forum(self, request, queryset):
        contador = 0
        for circulo in queryset:
            if circulo.grupo is None:
                contador += 1
                circulo.grupo = Grupo.objects.create(nome=circulo.titulo, descricao=circulo.descricao)
                circulo.save()
                for cmembro in circulo.circulomembro_set.all():
                    if cmembro.membro.usuario and not cmembro.grupousuario:
                        cmembro.grupousuario = GrupoUsuario.objects.create(grupo=circulo.grupo, usuario=cmembro.membro.usuario, admin=cmembro.administrador)
                        cmembro.save()
        self.message_user(request, 'Total de Fórums criados: %d' % contador)
    criar_forum.short_description = u'Criar Fórum de Discussão'

    def get_form(self, request, obj=None, **kwargs):
        defaults = {
            "form": self.form,
            "fields": flatten_fieldsets(self.get_fieldsets(request, obj)),
            "exclude": self.get_readonly_fields(request, obj),
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return modelform_factory(self.model, **defaults)

    def enviar_convite_evento(self, request, id_evento):
        evento = get_object_or_404(CirculoEvento, pk=id_evento)

        dt_evento = evento.dt_evento
        sendmail(
            subject=u'Convite - %s - %s - %s às %s' % (evento.circulo.titulo, evento.nome, _date(dt_evento, 'd \d\e F \d\e Y'), _date(dt_evento, 'H:i'),),
            bcc=evento.circulo.circulomembro_set.exclude(membro__status_email__in=('S', 'O')).values_list('membro__email', flat=True),
            template='emails/evento-convite.html',
            params={
                'evento': evento,
            },
        )
        messages.info(request, u'Os emails estão sendo enviados!')
        return HttpResponseRedirect(reverse('admin:cadastro_circulo_change', args=(evento.circulo.pk, )))

    def incluir_membros_auto(self, request, id_circulo):
        circulo = get_object_or_404(Circulo, pk=id_circulo)
        if circulo.tipo == 'R' or (circulo.tipo == 'S' and circulo.uf):
            membros_ja_cadastrados_pks = circulo.circulomembro_set.all().values_list('membro', flat=True)
            membros = Membro.objects.filter(uf=circulo.uf).exclude(pk__in=membros_ja_cadastrados_pks)
            if circulo.municipio:
                membros = membros.filter(municipio=circulo.municipio)
            for membro in membros:
                CirculoMembro(circulo=circulo, membro=membro).save()

                # Log
                user = User.objects.get_or_create(username="sys")[0]
                # Log do membro
                LogEntry.objects.log_action(
                    user_id = user.pk,
                    content_type_id = ContentType.objects.get_for_model(membro).pk,
                    object_id = membro.pk,
                    object_repr = u"%s" % membro,
                    action_flag = CHANGE,
                    change_message = u'Membro se inscreveu no Círculo %s.' % circulo
                )
                # Log do círculo
                LogEntry.objects.log_action(
                    user_id = user.pk,
                    content_type_id = ContentType.objects.get_for_model(circulo).pk,
                    object_id = circulo.pk,
                    object_repr = u"%s" % circulo,
                    action_flag = CHANGE,
                    change_message = u'Membro %s se inscreveu.' % membro
                )
            messages.info(request, u'%s Membros foram adicionados a este Círculo!' % membros.count())
            return HttpResponseRedirect(reverse('admin:cadastro_circulo_change', args=(circulo.pk, )))

        messages.error(request, u'Esta ação não é permitida para Círculos que não são Regional ou Esfera!')
        return HttpResponseRedirect(reverse('admin:cadastro_circulo_change', args=(circulo.pk, )))

    def criar_pagina(self, request, id_circulo):
        circulo = get_object_or_404(Circulo, pk=id_circulo)
        # Se não tiver Circulo.section cria uma Section e associa ao Circulo
        if not circulo.section:
            section = Section(title=circulo.titulo, header='', template='section-circulo.html')
            if circulo.imagem:
                section.header = u'<img src="%s" width="100%%">' % circulo.imagem.url
            section.save()
            circulo.section = section
            circulo.save()

            # Criar URLMigrate
            URLMigrate(
                old_url=circulo.get_absolute_url(),
                new_url=section.get_absolute_url(),
                redirect_type='H',
            ).save()

        messages.info(request, u'Página criada. <a href="%s">Clique aqui</a> para inserir o seu primeiro artigo.' % reverse('admin:cadastro_articlecadastro_add'))
        return HttpResponseRedirect(reverse('admin:cadastro_circulo_change', args=(circulo.pk, )))

    def get_urls(self):
        urls_originais = super(CirculoAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^(?P<id_evento>\d+)/enviar-convite/$', self.wrap(self.enviar_convite_evento), name='cadastro_circulo_enviar_convite_evento'),
            url(r'^(?P<id_circulo>\d+)/incluir-membros-auto/$', self.wrap(self.incluir_membros_auto), name='cadastro_circulo_incluir_membros_auto'),
            url(r'^(?P<id_circulo>\d+)/criar-pagina/$', self.wrap(self.criar_pagina), name='cadastro_circulo_criar_pagina'),
        )
        return urls_customizadas + urls_originais

    def get_buttons(self, request, object_id):
        buttons = super(CirculoAdmin, self).get_buttons(request, object_id)
        obj = self.get_object(request, object_id)
        if obj:
            if obj.tipo == 'R' or (obj.tipo == 'S' and obj.uf):
                buttons.append(PowerButton(url=reverse('admin:cadastro_circulo_incluir_membros_auto', kwargs={'id_circulo': obj.pk}), label=u'Adicionar Membros'))
            if not obj.section:
                buttons.append(PowerButton(url=reverse('admin:cadastro_circulo_criar_pagina', kwargs={'id_circulo': obj.pk}), label=u'Criar página do Círculo'))
            else:
                buttons.append(PowerButton(url=reverse('admin:cadastro_articlecadastro_changelist'), label=u'Gerenciar Artigos'))
        return buttons

    def save_model(self, request, obj, form, change):
        super(CirculoAdmin, self).save_model(request, obj, form, change)
        if obj.section:
            URLMigrate.objects.filter(new_url=obj.section.get_absolute_url()).update(old_url=obj.get_absolute_url())

#        if not change:
#            try:
#                membro = Membro.objects.get(usuario=request.user)
#                CirculoMembro(
#                    membro = membro,
#                    circulo = obj,
#                    administrador = True,
#                ).save()
#            except Membro.DoesNotExist:
#                return

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
    list_display = ('assunto', 'tipo', 'fonte', 'autor', 'status', 'dtenvio', 'qtde_envio', 'qtde_erros', 'qtde_views',)
    list_filter = ('tipo', 'dtenvio', )
    multi_search = (
        ('q1', u'Assunto', ['assunto', ]),
        ('q2', u'Lista', ['lista__nome', ]),
        ('q3', u'Círculo', ['circulo_membro__titulo', 'circulo_visitante__titulo', ]),
    )
    fieldsets = [
        (None, { 'fields': ['tipo', 'lista', 'circulo_membro', 'circulo_visitante', 'assunto', 'template', 'template_html', ], },),
    ]
    fieldsets_readonly = [
        (None, { 'fields': ['tipo', 'lista', 'circulo_membro', 'circulo_visitante', 'assunto', ('qtde_envio', 'qtde_erros', 'qtde_views',), 'status', 'dtenvio', 'template', 'template_html',], },),
    ]
    readonly_fields = ('template_html', )
    radio_fields = {'tipo': admin.HORIZONTAL}

    def get_fieldsets(self, request, obj=None):
        if obj and obj.dtenvio:
            return self.fieldsets_readonly
        return self.fieldsets

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.dtenvio:
            return ('tipo', 'lista', 'circulo_membro', 'circulo_visitante', 'qtde_envio', 'status', 'dtenvio', 'qtde_erros', 'qtde_views', 'template_html', )
        return ('template_html', )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "lista":
                kwargs["queryset"] = Lista.objects.none()
                if request.user.groups.filter(name__in=(u'Mail Marketing', u'Comissão')).exists():
                    kwargs["queryset"] = Lista.objects.filter(status='A')
            if db_field.name == "circulo_membro":
                circulo_ids = CirculoMembro.objects.filter(membro__usuario=request.user, administrador=True).values_list('circulo', flat=True)
                kwargs["queryset"] = Circulo.objects.filter(pk__in=circulo_ids)
            if db_field.name == "circulo_visitante":
                circulo_ids = CirculoMembro.objects.filter(membro__usuario=request.user, administrador=True).values_list('circulo', flat=True)
                kwargs["queryset"] = Circulo.objects.filter(pk__in=circulo_ids, tipo='S').distinct()
        return super(CampanhaAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if  not request.user.is_superuser:
            if db_field.name == "tipo":
                if not request.user.groups.filter(name__in=(u'Mail Marketing', u'Comissão')).exists():
                    kwargs['choices'] = (
                        ('M', u'Membros'),
                        ('V', u'Visitantes'),
                    )
        return super(CampanhaAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    def teste_de_envio(self, request, id_campanha):
        campanha = get_object_or_404(Campanha, pk=id_campanha)
        if request.method == 'POST' and request.POST.get('email'):
            email = request.POST.get('email')
            campanha.send_email_test(to=[email, ])
            messages.info(request, u'Email enviado com sucesso!')
        else:
            messages.error(request, u'Preencha corretamento o campo email na hora de testar o envio.')
        return HttpResponseRedirect(reverse('admin:cadastro_campanha_change', args=(id_campanha, )))

    def processar(self, request, id_campanha):
        # Verificar se existe outra campanha sendo processada
        if Campanha.objects.filter(status='P').exists():
            messages.error(request, u'Já existe uma campanha sendo processada. ')
            return HttpResponseRedirect(reverse('admin:cadastro_campanha_change', args=(id_campanha, )))

        campanha = get_object_or_404(Campanha, pk=id_campanha)
         # Verificar img 1x1 existe
        if not os.path.isfile(u"%s/site/img/1x1.png" % settings.STATIC_ROOT):
            messages.error(request, u'Não é possível enviar a campanha! Verifique se o arquivo %s/site/img/1x1.png existe.' % settings.STATIC_ROOT)
            return HttpResponseRedirect(reverse('admin:cadastro_campanha_change', args=(id_campanha, )))

        if campanha.status == 'P':
            messages.error(request, u'A campanha já está sendo processada. ')
        elif campanha.status == 'F':
            messages.error(request, u'A campanha já foi finalizada. ')
        elif campanha.status == 'E':
            campanha.status = 'P'
            campanha.save()
            campanha.send_emails(request.user, resumir=False)
            messages.info(request, u'Os emails estão sendo enviados!')
        else:
            campanha.status = 'P'
            campanha.save()
            campanha.send_emails(request.user, resumir=True)
            messages.info(request, u'Processamento retomado. Os emails estão sendo enviados!')
        return HttpResponseRedirect(reverse('admin:cadastro_campanha_change', args=(id_campanha, )))

    def interromper(self, request, id_campanha):
        campanha = get_object_or_404(Campanha, pk=id_campanha)
        if campanha.status == 'P':
            campanha.status = 'I'
            campanha.save()
        else:
            messages.error(request, u'Não é possível interromper essa campanha. ')
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
            autor = request.user
        )
        messages.info(request, u'Cópia da campanha %s criada com sucesso!' % campanha)
        return HttpResponseRedirect(reverse('admin:cadastro_campanha_change', args=(nova_campanha.pk, )))

    def get_urls(self):
        urls_originais = super(CampanhaAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^(?P<id_campanha>\d+)/teste-de-envio/$', self.wrap(self.teste_de_envio), name='cadastro_campanha_teste_de_envio'),
            url(r'^(?P<id_campanha>\d+)/processar/$', self.wrap(self.processar), name='cadastro_campanha_processar'),
            url(r'^(?P<id_campanha>\d+)/interromper/$', self.wrap(self.interromper), name='cadastro_campanha_interromper'),
            url(r'^(?P<id_campanha>\d+)/template/$', self.wrap(self.template), name='cadastro_campanha_template'),
            url(r'^(?P<id_campanha>\d+)/copiar/$', self.wrap(self.copiar), name='cadastro_campanha_copiar'),
        )
        return urls_customizadas + urls_originais

    def get_buttons(self, request, object_id):
        buttons = super(CampanhaAdmin, self).get_buttons(request, object_id)
        obj = self.get_object(request, object_id)
        if obj:
            buttons.append(PowerButton(url='?lightbox[width]=280&lightbox[height]=90#box-teste_de_envio', attrs={'class': 'historylink lightbox', }, label=u'Teste de Envio'))
            if obj.status in ('E', 'I', 'R'):
                buttons.append(PowerButton(url=reverse('admin:cadastro_campanha_processar', kwargs={'id_campanha': object_id, }), label=u'Processar'))
            if obj.status == 'P':
                buttons.append(PowerButton(url=reverse('admin:cadastro_campanha_interromper', kwargs={'id_campanha': object_id, }), label=u'Interromper'))
            buttons.append(PowerButton(url=reverse('admin:cadastro_campanha_copiar', kwargs={'id_campanha': object_id, }), label=u'Copiar'))
        return buttons

    def save_model(self, request, obj, form, change):
        if not obj.autor:
            obj.autor = request.user
        return super(CampanhaAdmin, self).save_model(request, obj, form, change)

    def queryset(self, request):
        qs = super(CampanhaAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(autor=request.user)

class ColetaArticulacaoAdmin(PowerModelAdmin):
    list_display = ('UF', 'municipio', 'zona', 'articulador', 'articulador_email')
    list_filter = ('UF', 'municipio__nome', )
    multi_search = (
        ('q1', u'Nome', ['articulador__nome', ]),
        ('q2', u'Email', ['articulador__email', ]),
    )
    fieldsets = [
        (None, { 'fields': ['UF', 'municipio', 'zona', 'articulador',  ], },),
    ]
    raw_id_fields = ('articulador', )
    ordering = ('UF', )

    queryset_filter = {
        'municipio__nome': 'municipio_filter',
    }
    def municipio_filter(self, request):
        if request.GET.get('UF__id_ibge__exact'):
            return Municipio.objects.filter(uf__id_ibge=request.GET.get('UF__id_ibge__exact'))
        return Municipio.objects.none()
    municipio_filter.short_description = u'Município'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.groups.filter(name=u'Articulador').exists():
            if db_field.name == "UF":
                uf_ids = ColetaArticulacao.objects.filter(articulador__usuario=request.user).values_list('UF', flat=True)
                kwargs["queryset"] = UF.objects.filter(pk__in=uf_ids)
        return super(ColetaArticulacaoAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def queryset(self, request):
        qs = super(ColetaArticulacaoAdmin, self).queryset(request)
        if request.user.groups.filter(name=u'Articulador').exists():
            uf_ids = ColetaArticulacao.objects.filter(articulador__usuario=request.user).values_list('UF', flat=True)
            return qs.filter(UF__pk__in=uf_ids)
        return qs

class CandidaturaInline(admin.TabularInline):
    model = Candidatura
    extra = 1
    verbose_name_plural = u'Candidaturas'
    raw_id_fields = ('candidato', )

class ColigacaoAdmin(PowerModelAdmin):
    list_display = ('UF', 'municipio', 'partidos',)
    list_filter = ('UF', 'municipio__nome', )
    fieldsets = [
        (None, { 'fields': ['UF', 'municipio', 'partidos',  ], },),
    ]
    ordering = ('UF', )
    inlines = (CandidaturaInline, )

    queryset_filter = {
        'municipio__nome': 'municipio_filter',
    }

    def municipio_filter(self, request):
        if request.GET.get('UF__id_ibge__exact'):
            return Municipio.objects.filter(uf__id_ibge=request.GET.get('UF__id_ibge__exact'))
        return Municipio.objects.none()
    municipio_filter.short_description = u'Município'


class SectionItemInline(admin.TabularInline):
    model = SectionItem
    extra = 1
    verbose_name_plural = u'Seções'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "section":
            section_ids = Circulo.objects.values_list('section', flat=True)
            kwargs["queryset"] = Section.objects.filter(pk__in=section_ids)
            if not request.user.is_superuser:
                section_ids = CirculoMembro.objects.filter(membro__usuario=request.user, administrador=True).values_list('circulo__section', flat=True)
                kwargs["queryset"] = Section.objects.filter(pk__in=section_ids)
        return super(SectionItemInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
class ArticleCadastroAdmin(PowerModelAdmin):
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
            'fields': ['link', ('title', 'slug'), 'header', 'content', 'is_active', 'upload', ]
        }),
    )
    form = ArticleCadastroForm
    inlines = (SectionItemInline, )

    def has_change_permission(self, request, obj=None):
        return super(ArticleCadastroAdmin, self).has_change_permission(request, obj) or request.user.has_perm('cms.' + self.opts.get_change_permission())

    def has_add_permission(self, request):
        return super(ArticleCadastroAdmin, self).has_add_permission(request) or request.user.has_perm('cms.' + self.opts.get_add_permission())

    def save_model(self, request, obj, form, change):
        obj.author = request.user
        # Salvar imagem, usando a view do ckeditor
        if request.FILES.get('upload'):
            from ckeditor.views import upload

            url = upload(request).content
            obj.header = u'<img src="%s" style="width: 50px; height: 37px;"/>%s' % (url, obj.header, )
            obj.content = u'<img src="%s" style="width: 270px; height: 152px; margin: 10px; float: left;"/>%s' % (url, obj.content, )
        super(ArticleCadastroAdmin, self).save_model(request, obj, form, change)

        # Se for link colocar o slug == pk, e captura o titulo, chamada e imagem do artigo
        if form.cleaned_data.get('link'):
            #try:
            html = requests.get(form.cleaned_data.get('content')).text
            soup = BeautifulSoup(html)
            obj.title = u'%s' % soup.title.string
            obj.header = u''
            if soup.select('meta[property="og:image"]'):
                obj.header += u'<img style="width: 270px; height: 152px; margin: 10px; float: left;" src="%s">' % soup.select('meta[property="og:image"]')[0].get('content')
            if soup.select('meta[name="description"]'):
                obj.header += u'%s' % soup.select('meta[name="description"]')[0].get('content')
            #except: pass
            obj.slug = obj.pk
            obj.save()

    def queryset(self, request):
        qs = super(ArticleCadastroAdmin, self).queryset(request)
        qs = qs.exclude(sectionitem__section__circulo=None)
        section_ids = CirculoMembro.objects.filter(membro__usuario=request.user, administrador=True).values_list('circulo__section', flat=True)
        if not request.user.is_superuser:
            qs = qs.filter(sectionitem__section__pk__in=section_ids)
        return qs

admin.site.register(ArticleCadastro, ArticleCadastroAdmin)
admin.site.register(CirculoEvento)
admin.site.register(UF)
admin.site.register(ColetaArticulacao, ColetaArticulacaoAdmin)
admin.site.register(Coligacao, ColigacaoAdmin)

admin.site.register(Campanha, CampanhaAdmin)
