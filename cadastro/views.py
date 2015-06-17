# -*- coding: utf-8 -*-
from django.views.generic import FormView, TemplateView
from django.core.urlresolvers import reverse
from django.contrib import messages

from models import Circulo
from municipios.models import UF
from forms import NewsletterForm, MembroForm


class IndexView(TemplateView):
    template_name = 'site/index.html'

    def get_context_data(self, **kwargs):
        circulos = {}
        for uf in UF.objects.all().order_by('nome'):
            queryset = Circulo.objects.filter(uf=uf)
            if queryset:
                cidades = []
                for query in queryset:
                    if query.site_externo:
                        cidades.append(u'<a href="%s" target="_blank">%s</a>' % (query.site_externo, query.municipio, ))
                    else:
                        cidades.append(query.municipio)
                circulos[uf.nome] = u"Cidades: %s" % (u", ".join(cidades))
            else:
                circulos[uf.nome] = u"Ainda não existe nenhum círculo em seu estado."
        kwargs['circulos'] = circulos
        return super(IndexView, self).get_context_data(**kwargs)


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