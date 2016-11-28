# -*- coding: utf-8 -*-
from django.views.generic import FormView, TemplateView, View, DetailView, RedirectView
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.http import int_to_base36, base36_to_int
from django.utils.crypto import constant_time_compare, salted_hmac
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import get_text_list
from django.utils.encoding import force_unicode

from models import Circulo, Membro, CirculoMembro, Pessoa, Campanha, Lista, ListaCadastro, CirculoPendente
from municipios.models import UF
from forms import NewsletterForm, MembroForm, FiliadoForm, AtualizarCadastroLinkForm, AtualizarCadastroFiliadoForm, \
    AtualizarCadastroMembroForm, ConsultaForm, CirculoPendenteForm
from cadastro.telegram import bot
from cms.email import sendmail
from utils.stdlib import get_client_ip

from datetime import date
import cStringIO as StringIO
from PIL import Image
import operator
import json



class NewsletterView(FormView):
    template_name = 'cadastro/newsletter.html'
    template_success_name = 'cadastro/bem-vindo.html'
    form_class = NewsletterForm

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Cadastro realizado com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            context={
                'title': u'Cadastro Efetuado.',
                'msg': u'Você receberá um email para que possa confirmar seus dados.',
            }
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(NewsletterView, self).form_invalid(form)


class MeuPerfilView(TemplateView):
    template_name = 'cadastro/meu-perfil.html'

    def get(self, request, *args, **kwargs):
        if not request.user.membro.exists():
            messages.error(request, u'Não há nenhum Membro associado a esse usuário!')
            return HttpResponseRedirect(reverse('home'))
        return super(MeuPerfilView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MeuPerfilView, self).get_context_data(**kwargs)
        context['membro'] = self.request.user.membro.all()[0]
        return context


class TelegramView(RedirectView):
    def get(self, request, *args, **kwargs):
        if not request.user.membro.exists():
            messages.error(request, u'Não há nenhum Membro associado a esse usuário!')
            return HttpResponseRedirect(reverse('home'))
        membro = request.user.membro.all()[0]
        membro.telegram_id = request.GET.get('telegram_id')
        membro.save()
        messages.info(request, u'Telegram associado com sucesso!')
        bot.sendMessage(membro.telegram_id, u'Telegram associado com sucesso ao usuário Raiz!')
        return HttpResponseRedirect(reverse('meu_perfil'))


class MembroView(FormView):
    template_name = 'cadastro/membro.html'
    template_success_name = 'cadastro/bem-vindo.html'
    form_class = MembroForm

    def get(self, request, *args, **kwargs):
        if request.GET.get('email'):
            json = {'msg': ''}
            if Membro.objects.filter(email=request.GET.get('email'), filiado=True).exists():
                json['msg'] = u'Você já está registrado no site como Pré-filiado. Para editar os seus dados <a href="%s?email=%s">clique aqui</a>.' % (reverse('atualizar_cadastro_link'), request.GET.get('email'))
            elif Membro.objects.filter(email=request.GET.get('email')).exists():
                json['msg'] = u'Já existe um cadastro com esse email. Faça login no site para que possa alterar seus dados ou <a href="%s?email=%s">clique aqui</a>.' % (reverse('atualizar_cadastro_link'), request.GET.get('email'))
            return HttpResponse(simplejson.dumps(json, ensure_ascii=False), mimetype='text/javascript; charset=utf-8')

        return super(MembroView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Cadastro realizado com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            context={
                'title': u'Cadastro Efetuado.',
                'msg': u'Você receberá um email para que possa confirmar seus dados.',
            }
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        # TODO: Monitorar issue https://github.com/josircg/raizcidadanista/issues/52
        errors = dict(form.non_field_errors())
        errors.update(dict(form.errors))
        sendmail(
            subject=u'[LOG] Raiz Movimento Cidadanista - Tentativa de cadastro de Colaborador',
            to=[email for name, email in settings.ADMINS],
            template='emails/error.html',
            params={
                'title': u'Tentativa de cadastro de Colaborador',
                'error': u'<b>Erros:</b> %s<br><br><b>Dados:</b> %s' % (errors, dict(form.data)),
            },
        )
        return super(MembroView, self).form_invalid(form)


class MembroEntrarCirculoView(View):
    def get(self, request, circulo_id, *args, **kwargs):
        circulo = get_object_or_404(Circulo, pk=circulo_id)
        membro = get_object_or_404(Membro, usuario=request.user)
        if not circulo.permitecadastro:
            raise PermissionDenied

        cm, created = CirculoMembro.objects.get_or_create(circulo=circulo, membro=membro)

        if created:
            # Log do membro
            LogEntry.objects.log_action(
                user_id = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(membro).pk,
                object_id = membro.pk,
                object_repr = u"%s" % membro,
                action_flag = CHANGE,
                change_message = u'Membro adicionado automaticamente ao Círculo %s.' % circulo
            )
            # Log do círculo
            LogEntry.objects.log_action(
                user_id = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(circulo).pk,
                object_id = circulo.pk,
                object_repr = u"%s" % circulo,
                action_flag = CHANGE,
                change_message = u'Membro %s adicionado automaticamente.' % membro
            )
            messages.info(request, u'Você agora faz parte do Círculo %s.' % circulo.titulo)
        else:
            messages.info(request, u'Você já fazia parte do Círculo %s.' % circulo.titulo)
        if circulo.site_externo:
            return HttpResponseRedirect(circulo.site_externo)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


class AtualizarCadastroLinkView(FormView):
    template_name = 'cadastro/atualizar-cadastro-link.html'
    template_success_name = 'cadastro/bem-vindo.html'
    template_email_name = 'emails/atualizar-cadastro.html'
    form_class = AtualizarCadastroLinkForm

    def get(self, request, *args, **kwargs):
        if request.GET.get('filiado') == 'true':
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            if form.is_valid():
                form.sendmail(template_email_name=self.template_email_name)
                return self.response_class(
                    request=self.request,
                    template=self.template_success_name,
                    context={
                        'title': u'Atualização de Cadastro do Raíz',
                        'msg': u'Um email acaba de ser enviado com as instruções para edição dos seus dados',
                    }
                )
        return super(AtualizarCadastroLinkView, self).get(request, *args, **kwargs)


    def get_form_kwargs(self):
        kwargs = super(AtualizarCadastroLinkView, self).get_form_kwargs()
        kwargs['initial'] = self.request.GET
        if self.request.GET.get('filiado') == 'true':
            kwargs['data'] = self.request.GET
        return kwargs

    def form_valid(self, form):
        form.sendmail(template_email_name=self.template_email_name)
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            context={
                'title': u'Atualização de Cadastro do Raíz',
                'msg': u'Um email acaba de ser enviado com as instruções para edição dos seus dados',
            }
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(AtualizarCadastroLinkView, self).form_invalid(form)


class RecadastramentoView(TemplateView):
    template_name = 'cadastro/recadastramento.html'
    template_success_name = 'cadastro/bem-vindo.html'

    def get_instance(self, request, uidb36, ts_b36, token):
        def create_token(instance):
            key_salt = "cadastro.forms.RecadastramentoView"
            value = u'%s%s' % (instance.pk, instance.email,)
            return salted_hmac(key_salt, value).hexdigest()[::2]

        try:
            uid_int = base36_to_int(uidb36)

            # Link só funciona 3 dia
            ts_int = base36_to_int(ts_b36)
            if ts_int+3 < (date.today() - date(2001, 1, 1)).days:
                return None

            instance = Membro.objects.get(id=uid_int)
        except (ValueError, Membro.DoesNotExist):
            return None
        if not constant_time_compare(create_token(instance), token):
            return None

        return instance

    def post(self, request, uidb36, ts_b36, token, *args, **kwargs):
        self.instance = self.get_instance(request, uidb36, ts_b36, token)
        if not self.instance:
            return self.response_class(
                request=self.request,
                template=self.template_success_name,
                context={
                    'title': u'RECADASTRAMENTO RAIZ',
                    'msg': u'Você demorou muito para realizar o recadastramento.',
                }
            )

        if request.POST.get('action'):
            if request.POST.get('action') == 'confirmar':
                # FIXBUG não estava salvando!
                Membro.objects.filter(pk=self.instance.pk).update(confirmado=True)
                self.instance = self.get_instance(request, uidb36, ts_b36, token)
                messages.info(request, u'Cadastro como pré-filiado confirmado.')
                LogEntry.objects.log_action(
                    user_id = User.objects.get_or_create(username="sys")[0].pk,
                    content_type_id = ContentType.objects.get_for_model(self.instance).pk,
                    object_id = self.instance.pk,
                    object_repr = u"%s" % self.instance,
                    action_flag = CHANGE,
                    change_message = u'[RECAD] Usuário confirmou o cadastro como pré-filiado com o IP %s.' % get_client_ip(request)
                )
                # Fazer o login e redirecionara para o Meu Perfil
                if self.instance.usuario:
                    self.instance.usuario.backend='django.contrib.auth.backends.ModelBackend'
                    login(request, self.instance.usuario)
                    return HttpResponseRedirect(reverse('meu_perfil'))

            elif request.POST.get('action') == 'colaborador':
                # FIXBUG não estava salvando!
                Membro.objects.filter(pk=self.instance.pk).update(filiado=False)
                self.instance = self.get_instance(request, uidb36, ts_b36, token)
                messages.info(request, u'Você foi marcado como Colaborador.')
                LogEntry.objects.log_action(
                    user_id = User.objects.get_or_create(username="sys")[0].pk,
                    content_type_id = ContentType.objects.get_for_model(self.instance).pk,
                    object_id = self.instance.pk,
                    object_repr = u"%s" % self.instance,
                    action_flag = CHANGE,
                    change_message = u'[RECAD] Usuário passou a ser colaborador.'
                )
            elif request.POST.get('action') == 'filiado':
                # FIXBUG não estava salvando!
                Membro.objects.filter(pk=self.instance.pk).update(filiado=True)
                self.instance = self.get_instance(request, uidb36, ts_b36, token)
                messages.info(request, u'Você foi marcado como pré-filiado.')
                LogEntry.objects.log_action(
                    user_id = User.objects.get_or_create(username="sys")[0].pk,
                    content_type_id = ContentType.objects.get_for_model(self.instance).pk,
                    object_id = self.instance.pk,
                    object_repr = u"%s" % self.instance,
                    action_flag = CHANGE,
                    change_message = u'[RECAD] Usuário passou a ser pré-filiado.'
                )
            elif request.POST.get('action') == 'sair':
                # FIXBUG não estava salvando!
                Membro.objects.filter(pk=self.instance.pk).update(status_email='O', status='C', confirmado=True, filiado=False)
                # Remover a pessoa de todos os círculos.
                CirculoMembro.objects.filter(membro=self.instance).delete()
                self.instance = self.get_instance(request, uidb36, ts_b36, token)
                messages.info(request, u'Desligamento efetuado com sucesso.')
                LogEntry.objects.log_action(
                    user_id = User.objects.get_or_create(username="sys")[0].pk,
                    content_type_id = ContentType.objects.get_for_model(self.instance).pk,
                    object_id = self.instance.pk,
                    object_repr = u"%s" % self.instance,
                    action_flag = CHANGE,
                    change_message = u'[RECAD] Usuário pediu desligamento.'
                )
                return HttpResponseRedirect('/')
        return self.response_class(
            request=self.request,
            template=self.template_name,
            context=self.get_context_data(**kwargs)
        )

    def get(self, request, uidb36, ts_b36, token, *args, **kwargs):
        self.instance = self.get_instance(request, uidb36, ts_b36, token)
        if not self.instance:
            return self.response_class(
                request=self.request,
                template=self.template_success_name,
                context={
                    'title': u'RECADASTRAMENTO RAIZ',
                    'msg': u'Você demorou muito para realizar o recadastramento.',
                }
            )

        if self.instance.confirmado:
            messages.info(request, u'O seu recadastramento já foi efetuado.')
            return HttpResponseRedirect(reverse('meu_perfil'))

        LogEntry.objects.log_action(
            user_id = User.objects.get_or_create(username="sys")[0].pk,
            content_type_id = ContentType.objects.get_for_model(self.instance).pk,
            object_id = self.instance.pk,
            object_repr = u"%s" % self.instance,
            action_flag = CHANGE,
            change_message = u'[RECAD] Usuário respondeu ao recadastramento.'
        )
        return super(RecadastramentoView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(RecadastramentoView, self).get_context_data(**kwargs)
        context['membro'] = self.instance
        return context


class AtualizarCadastroView(FormView):
    template_name_filiado = 'cadastro/atualizar-cadastro-filiado.html'
    template_name_membro = 'cadastro/atualizar-cadastro-membro.html'
    template_success_name = 'cadastro/bem-vindo.html'
    form_class_filiado = AtualizarCadastroFiliadoForm
    form_class_membro = AtualizarCadastroMembroForm

    def get_instance(self, request, uidb36, ts_b36, token):
        def create_token(instance):
            key_salt = "cadastro.forms.AtualizarCadastroLinkForm"
            value = u'%s%s' % (instance.pk, instance.email,)
            return salted_hmac(key_salt, value).hexdigest()[::2]

        try:
            uid_int = base36_to_int(uidb36)

            # Link só funciona 3 dia
            ts_int = base36_to_int(ts_b36)
            if ts_int+3 < (date.today() - date(2001, 1, 1)).days:
                return None

            instance = Membro.objects.get(id=uid_int)
        except (ValueError, Membro.DoesNotExist):
            return None
        if not constant_time_compare(create_token(instance), token):
            return None

        return instance

    def get_template_names(self):
        if self.instance.filiado or self.request.GET.get('filiado'):
            return [self.template_name_filiado]
        return [self.template_name_membro]

    def get_form_class(self):
        if self.instance.filiado or self.request.GET.get('filiado'):
            return self.form_class_filiado
        return self.form_class_membro

    def get(self, request, uidb36, ts_b36, token, *args, **kwargs):
        self.instance = self.get_instance(request, uidb36, ts_b36, token)
        if not self.instance:
            return self.response_class(
                request=self.request,
                template=self.template_success_name,
                context={
                    'title': u'RECADASTRAMENTO RAIZ',
                    'msg': u'Você demorou muito para realizar a atualização cadastral.<br><a href="%s">Clique aqui</a> para solicitar uma nova atualização.' % reverse('atualizar_cadastro_link'),
                }
            )
        return super(AtualizarCadastroView, self).get(request, *args, **kwargs)

    def post(self, request, uidb36, ts_b36, token, *args, **kwargs):
        self.instance = self.get_instance(request, uidb36, ts_b36, token)
        if not self.instance:
            return self.response_class(
                request=self.request,
                template=self.template_success_name,
                context={
                    'title': u'RECADASTRAMENTO RAIZ',
                    'msg': u'Você demorou muito para realizar a atualização cadastral.<br><a href="%s">Clique aqui</a> para solicitar uma nova atualização.' % reverse('atualizar_cadastro_link'),
                }
            )
        return super(AtualizarCadastroView, self).post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AtualizarCadastroView, self).get_form_kwargs()
        kwargs['instance'] = self.instance
        return kwargs

    def construct_change_message(self, request, form):
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
                change_message.append(u'Modificado %s.' % get_text_list(changed_data_msg, 'e'))
        change_message = ' '.join(change_message)
        return change_message or u'Nenhum campo alterado.'

    def form_valid(self, form):
        instance = form.save()
        LogEntry.objects.log_action(
            user_id = User.objects.get_or_create(username="sys")[0].pk,
            content_type_id = ContentType.objects.get_for_model(instance).pk,
            object_id = instance.pk,
            object_repr = u'%s' % instance,
            action_flag = CHANGE,
            change_message = self.construct_change_message(self.request, form)
        )
        messages.info(self.request, u"Cadastro atualizado com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            context={
                'title': u'Cadastro atualizado com sucesso!',
                'msg': u'Obrigado por atualizar o seu cadastro.<br><a href="/meus-talentos/">Cadastre também os seus talentos e como você se voluntariar para ajudar na Raiz</a>',
            }
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(AtualizarCadastroView, self).form_invalid(form)


class FiliadoView(FormView):
    template_name = 'cadastro/filiado.html'
    template_success_name = 'cadastro/bem-vindo.html'
    form_class = FiliadoForm

    def get(self, request, *args, **kwargs):
        if request.GET.get('email'):
            json = {'msg': ''}
            if Membro.objects.filter(email=request.GET.get('email'), filiado=True).exists():
                json['msg'] = u'Você já está registrado no site como filiado. Para editar os seus dados <a href="%s?email=%s">clique aqui</a>.' % (reverse('atualizar_cadastro_link'), request.GET.get('email'))
            elif Membro.objects.filter(email=request.GET.get('email')).exists():
                json['msg'] = u'Você já está registrado no site. Para editar os seus dados e se tornar um filiado, <a href="%s?email=%s&filiado=true">clique aqui</a>.' % (reverse('atualizar_cadastro_link'), request.GET.get('email'))
            return HttpResponse(simplejson.dumps(json, ensure_ascii=False), mimetype='text/javascript; charset=utf-8')
        if request.GET.get('cpf'):
            json = {'msg': ''}
            if Membro.objects.filter(cpf=request.GET.get('cpf'), filiado=True).exists():
                json['msg'] = u'Você já está registrado no site como filiado. Para editar os seus dados <a href="%s?cpf=%s">clique aqui</a>.' % (reverse('atualizar_cadastro_link'), request.GET.get('cpf'))
            elif Membro.objects.filter(cpf=request.GET.get('cpf')).exists():
                json['msg'] = u'Você já está registrado no site. Para editar os seus dados e se tornar um filiado, <a href="%s?cpf=%s&filiado=true">clique aqui</a>.' % (reverse('atualizar_cadastro_link'), request.GET.get('cpf'))
            return HttpResponse(simplejson.dumps(json, ensure_ascii=False), mimetype='text/javascript; charset=utf-8')
        return super(FiliadoView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Cadastro realizado com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            context={
                'title': u'Cadastro Efetuado.',
                'msg': u'Você receberá um email para que possa confirmar seus dados.<br><a href="/meus-talentos/">Cadastre também os seus talentos e como você se voluntariar para ajudar na Raiz</a>',
            }
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(FiliadoView, self).form_invalid(form)


class MembroConsulta(FormView):
    template_name = 'cadastro/consulta.html'
    form_class = ConsultaForm

    def form_valid(self, form):

        or_queries = [Q(**{'email__icontains': form.cleaned_data.get('nome')})]
        or_queries.append(reduce(operator.and_, [Q(**{'nome__icontains': bit}) for bit in form.cleaned_data.get('nome').split()]))
        queryset = Pessoa.objects.filter(reduce(operator.or_, or_queries)).distinct()

        if queryset.exists():
            for pessoa in queryset:
                tipo = u'Colaborador'
                try:
                    if pessoa.membro and pessoa.membro.filiado:
                        tipo = u'Filiado'
                except Membro.DoesNotExist: pass
                messages.info(self.request, u"%s (%s/%s) (%s)." % (pessoa.nome, pessoa.municipio or '-', pessoa.uf.uf or '-', tipo))
        else:
            messages.error(self.request, u'%s não encontrada!' % form.cleaned_data.get('nome'))
        return self.response_class(
            request=self.request,
            template=self.template_name,
            context={
                'form': self.form_class(),
            }
        )

class ValidarEmailView(TemplateView):
    template_name = 'cadastro/bem-vindo.html'
    def get(self, request, pessoa_id, *args, **kwargs):
        pessoa = get_object_or_404(Pessoa, pk=pessoa_id, email=request.GET.get('email'))
        pessoa.status_email = 'A'
        pessoa.save()
        LogEntry.objects.log_action(
            user_id = User.objects.get_or_create(username="sys")[0].pk,
            content_type_id = ContentType.objects.get_for_model(pessoa).pk,
            object_id = pessoa.pk,
            object_repr = u'%s' % pessoa,
            action_flag = CHANGE,
            change_message = u'Email validado'
        )

        if Lista.objects.filter(nome=u'Visitantes').exists():
            ListaCadastro(
                lista = Lista.objects.get(nome=u'Visitantes'),
                pessoa = pessoa,
            ).save()

        messages.info(self.request, u"Email validado com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_name,
            context={
                'title': u'Email validado com sucesso!',
                'msg': u'Obrigado por confirmar seus dados.',
            }
        )


class CampanhaView(DetailView):
    model = Campanha

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.qtde_views += 1
        self.object.save()

        response = HttpResponse(mimetype='image')
        img = Image.open(u"%s/site/img/1x1.png" % settings.STATIC_ROOT)
        img_temp = StringIO.StringIO()
        img.save(img_temp, 'JPEG')
        img_temp.seek(0)
        response.write(img_temp.getvalue())
        return response


class CadastroCirculoView(FormView):
    form_class = CirculoPendenteForm
    template_name = 'cadastro/cadastro-circulo.html'

    def get(self, request, *args, **kwargs):
        if request.is_ajax() and request.GET.get('atualizar'):
            obj = get_object_or_404(CirculoPendente, pk=request.GET.get('atualizar'), autor=request.user)
            json_response = {
                'titulo': obj.titulo,
                'descricao': obj.descricao,
                'dtcriacao': obj.dtcriacao,
                'tipo': obj.tipo,
                'uf': obj.uf.pk,
                'municipio': obj.municipio,
                'area_geografica': obj.area_geografica,
                'status': obj.status,
                'num_membros': obj.num_membros,
                'num_membros_coleta': obj.num_membros_coleta,
                'jardineiro_1_nome': obj.jardineiro_1_nome,
                'jardineiro_1_email': obj.jardineiro_1_email,
                'jardineiro_1_telefone': obj.jardineiro_1_telefone,
                'jardineiro_2_nome': obj.jardineiro_2_nome,
                'jardineiro_2_email': obj.jardineiro_2_email,
                'jardineiro_2_telefone': obj.jardineiro_2_telefone,
                'site_externo': obj.site_externo,
                'ferramentas': obj.ferramentas,
            }
            return HttpResponse(json.dumps(json_response), mimetype='application/json')
        if request.is_ajax() and request.GET.get('titulo'):
            json_response = {
                'existe': Circulo.objects.filter(titulo=request.GET.get('titulo')).exists(),
            }
            return HttpResponse(json.dumps(json_response), mimetype='application/json')
        if request.is_ajax() and request.GET.get('uf'):
            json_response = {
                'existe': Circulo.objects.filter(uf=request.GET.get('uf'), municipio=request.GET.get('municipio')).exists(),
            }
            return HttpResponse(json.dumps(json_response), mimetype='application/json')
        return super(CadastroCirculoView, self).get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CadastroCirculoView, self).get_form_kwargs()
        kwargs['request'] = self.request
        if self.request.POST.get('atualizar'):
            kwargs['instance'] = get_object_or_404(CirculoPendente, pk=self.request.POST.get('atualizar'), autor=self.request.user)
        return kwargs

    def form_valid(self, form):
        form.save()
        form.sendmail()
        messages.info(self.request, u"Cadastro realizado com sucesso!")

        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return HttpResponseRedirect(reverse('cadastro_circulo'))