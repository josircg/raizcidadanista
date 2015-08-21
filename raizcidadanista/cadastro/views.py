# -*- coding: utf-8 -*-
from django.views.generic import FormView, TemplateView
from django.core.urlresolvers import reverse
from django.contrib import messages

from models import Circulo
from municipios.models import UF
from forms import NewsletterForm, MembroForm


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
            using=self.template_engine,
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(MembroView, self).form_invalid(form)

class FiliadoView(FormView):
    template_name = 'cadastro/filiado.html'
    template_success_name = 'cadastro/bem-vindo.html'
    form_class = FiliadoForm

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Cadastro realizado com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            using=self.template_engine,
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(MembroView, self).form_invalid(form)
