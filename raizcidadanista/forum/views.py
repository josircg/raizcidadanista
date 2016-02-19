# -*- coding: utf-8 -*-
from django.views.generic import DetailView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.contrib import messages

from models import Grupo, Topico
from forms import AddTopicoForm



class GrupoView(DetailView):
    model = Grupo
    template_name = 'forum/grupo.html'
    form_class = AddTopicoForm

    def get_object(self, queryset=None):
        obj = super(GrupoView, self).get_object(queryset)
        if not obj.grupousuario_set.filter(usuario=self.request.user).exists():
            raise PermissionDenied()
        return obj

    def get(self, request, *args, **kwargs):
        self.form = self.form_class()
        return super(GrupoView, self).get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.form_class(self.request.POST)
        self.form.instance.grupo = self.object
        self.form.instance.criador = self.request.user
        if self.form.is_valid():
            self.form.save()
            messages.info(self.request, u'Tópico criado com sucesso!')
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super(GrupoView, self).get_context_data(**kwargs)

        topicos_list = self.object.topico_set.filter(status='A')
        paginator = Paginator(topicos_list, 10)

        page = self.request.GET.get('page')
        try:
            topicos = paginator.page(page)
        except PageNotAnInteger:
            topicos = paginator.page(1)
        except EmptyPage:
            topicos = paginator.page(paginator.num_pages)

        context['topicos'] = topicos
        context['form'] = self.form
        return context