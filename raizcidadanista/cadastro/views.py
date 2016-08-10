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
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType

from models import Circulo, Membro, CirculoMembro, Pessoa, Campanha, Lista, ListaCadastro
from municipios.models import UF
from forms import NewsletterForm, MembroForm, FiliadoForm, AtualizarCadastroLinkForm, AtualizarCadastroFiliadoForm, AtualizarCadastroMembroForm, ConsultaForm
from cadastro.telegram import bot

from datetime import date
import cStringIO as StringIO
from PIL import Image



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
                json['msg'] = u'Você já está registrado no site como filiado. Para editar os seus dados <a href="%s?email=%s">clique aqui</a>.' % (reverse('atualizar_cadastro_link'), request.GET.get('email'))
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
                    'title': u'Link inválido, tente novamente.',
                    'msg': u'Link inválido, tente novamente.',
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
                    'title': u'Link inválido, tente novamente.',
                    'msg': u'Link inválido, tente novamente.',
                }
            )
        return super(AtualizarCadastroView, self).post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AtualizarCadastroView, self).get_form_kwargs()
        kwargs['instance'] = self.instance
        return kwargs

    def form_valid(self, form):
        instance = form.save()
        LogEntry.objects.log_action(
            user_id = User.objects.get_or_create(username="sys")[0].pk,
            content_type_id = ContentType.objects.get_for_model(instance).pk,
            object_id = instance.pk,
            object_repr = u'%s' % instance,
            action_flag = CHANGE,
            change_message = u'Formulário de atualização de cadastro foi preenchido.'
        )
        messages.info(self.request, u"Cadastro atualizado com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            context={
                'title': u'Cadastro atualizado com sucesso!',
                'msg': u'Obrigado por atualizar o seu cadastro.',
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
                'msg': u'Você receberá um email para que possa confirmar seus dados.',
            }
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(FiliadoView, self).form_invalid(form)


class MembroConsulta(FormView):
    template_name = 'cadastro/consulta.html'
    form_class = ConsultaForm

    def form_valid(self, form):
        if Pessoa.objects.filter(Q(nome=form.cleaned_data.get('nome'))|Q(email=form.cleaned_data.get('nome'))).distinct().exists():
            messages.info(self.request, u"%s já está cadastrado." % form.cleaned_data.get('nome'))
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
