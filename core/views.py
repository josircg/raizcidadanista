# -*- coding: utf-8 -*-
from django.views.generic import FormView
from django.core.urlresolvers import reverse
from django.contrib import messages

from forms import MembroForm, MembroFundadorForm


class MembroView(FormView):
    template_name = 'site/membro.html'
    form_class = MembroForm

    def get_success_url(self):
        return reverse('membro')

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Membro cadastrado com sucesso!")
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return super(MembroView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(MembroView, self).form_invalid(form)


class MembroFundadorView(FormView):
    template_name = 'site/membro-fundador.html'
    form_class = MembroFundadorForm

    def get_success_url(self):
        return reverse('membro-fundador')

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u"Membro Fundador cadastrado com sucesso!")
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return super(MembroFundadorView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(MembroFundadorView, self).form_invalid(form)