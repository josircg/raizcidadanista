# -*- coding: utf-8 -*-
from django.views.generic import FormView, TemplateView
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.utils.http import int_to_base36, base36_to_int
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils import simplejson

from models import Circulo, Membro
from municipios.models import UF
from forms import NewsletterForm, MembroForm, FiliadoForm, FiliadoAtualizarLinkForm, FiliadoAtualizarForm


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
                'title': u'Bem vindo',
                'msg': u'Obrigado por se cadastrar!',
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
                'title': u'Bem vindo',
                'msg': u'Obrigado por se cadastrar!',
            }
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(MembroView, self).form_invalid(form)


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
                'title': u'Bem vindo',
                'msg': u'Obrigado por se cadastrar!',
            }
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(FiliadoView, self).form_invalid(form)
