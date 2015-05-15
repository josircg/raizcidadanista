# -*- coding: utf-8 -*-
from django.views.generic import FormView
from django.core.urlresolvers import reverse
from django.contrib import messages

from forms import NewsletterForm, MembroForm


class NewsletterView(FormView):
    template_name = 'site/newsletter.html'
    form_class = NewsletterForm

    def get_success_url(self):
        return reverse('newsletter')

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Cadastrado realizado com sucesso!")
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return super(NewsletterView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(NewsletterView, self).form_invalid(form)


class MembroView(FormView):
    template_name = 'site/membro.html'
    form_class = MembroForm

    def get_success_url(self):
        return reverse('membro')

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Cadastrado realizado com sucesso!")
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return super(MembroView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(MembroView, self).form_invalid(form)