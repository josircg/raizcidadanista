# -*- coding: utf-8 -*-
from django.views.generic import FormView, TemplateView, View, DetailView
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.http import int_to_base36, base36_to_int
from django.utils.crypto import constant_time_compare, salted_hmac
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.conf import settings

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType

from models import Circulo, Membro, CirculoMembro, Pessoa, Campanha
from municipios.models import UF
from forms import NewsletterForm, MembroForm, FiliadoForm, FiliadoAtualizarLinkForm, FiliadoAtualizarForm

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


class MembroView(FormView):
    template_name = 'cadastro/membro.html'
    template_success_name = 'cadastro/bem-vindo.html'
    form_class = MembroForm

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

        CirculoMembro.objects.create(circulo=circulo, membro=membro)

        messages.info(request, u'Você agora faz parte do Círculo %s.' % circulo.titulo)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


class FiliadoAtualizarLinkView(FormView):
    template_name = 'cadastro/filiado-atualizar-link.html'
    template_success_name = 'cadastro/bem-vindo.html'
    template_email_name = 'emails/filiado-atualizar.html'
    form_class = FiliadoAtualizarLinkForm

    def get_form_kwargs(self):
        kwargs = super(FiliadoAtualizarLinkView, self).get_form_kwargs()
        kwargs['initial'] = self.request.GET
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
        return super(FiliadoAtualizarLinkView, self).form_invalid(form)


class FiliadoAtualizarView(FormView):
    template_name = 'cadastro/filiado-atualizar.html'
    template_success_name = 'cadastro/bem-vindo.html'
    form_class = FiliadoAtualizarForm

    def get_instance(self, request, uidb36, token):
        def create_token(instance):
            key_salt = "cadastro.forms.FiliadoAtualizarLinkForm"
            value = u'%s%s' % (instance.pk, instance.email,)
            return salted_hmac(key_salt, value).hexdigest()[::2]

        try:
            uid_int = base36_to_int(uidb36)
            instance = Membro.objects.get(id=uid_int)
        except (ValueError, Membro.DoesNotExist):
            return None
        if not constant_time_compare(create_token(instance), token):
            return None

        return instance

    def get(self, request, uidb36, token, *args, **kwargs):
        self.instance = self.get_instance(request, uidb36, token)
        if not self.instance:
            return self.response_class(
                request=self.request,
                template=self.template_success_name,
                context={
                    'title': u'Link inválido, tente novamente.',
                    'msg': u'Link inválido, tente novamente.',
                }
            )
        return super(FiliadoAtualizarView, self).get(request, *args, **kwargs)

    def post(self, request, uidb36, token, *args, **kwargs):
        self.instance = self.get_instance(request, uidb36, token)
        if not self.instance:
            return self.response_class(
                request=self.request,
                template=self.template_success_name,
                context={
                    'title': u'Link inválido, tente novamente.',
                    'msg': u'Link inválido, tente novamente.',
                }
            )
        return super(FiliadoAtualizarView, self).post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(FiliadoAtualizarView, self).get_form_kwargs()
        kwargs['instance'] = self.instance
        return kwargs

    def form_valid(self, form):
        form.save()
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
        return super(FiliadoAtualizarView, self).form_invalid(form)


class FiliadoView(FormView):
    template_name = 'cadastro/filiado.html'
    template_success_name = 'cadastro/bem-vindo.html'
    form_class = FiliadoForm

    def get(self, request, *args, **kwargs):
        if request.GET.get('email'):
            json = {'msg': ''}
            if Membro.objects.filter(email=request.GET.get('email')).exists():
                json['msg'] = u'Você já está cadastrado. Deseja editar os seus dados atuais? <a href="%s?email=%s">Clique aqui</a>' % (reverse('filiado_atualizar_link'), request.GET.get('email'))
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
        img = Image.open(u"%s/img/1x1.png" % settings.MEDIA_ROOT)
        img_temp = StringIO.StringIO()
        img.save(img_temp, 'JPEG')
        img_temp.seek(0)
        response.write(img_temp.getvalue())
        return response
