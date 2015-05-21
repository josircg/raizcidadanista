# -*- coding: utf-8 -*-
from django.views.generic import FormView
from django.core.urlresolvers import reverse
from django.contrib import messages

from forms import NewsletterForm, MembroForm


class NewsletterView(FormView):
    template_name = 'site/newsletter.html'
    template_success_name = 'site/bem-vindo.html'
    form_class = NewsletterForm

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Cadastrado realizado com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            using=self.template_engine,
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(NewsletterView, self).form_invalid(form)


class MembroView(FormView):
    template_name = 'site/membro.html'
    template_success_name = 'site/bem-vindo.html'
    form_class = MembroForm

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Cadastrado realizado com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            using=self.template_engine,
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(MembroView, self).form_invalid(form)