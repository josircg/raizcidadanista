# -*- coding: utf-8 -*-
from django.views.generic import DetailView, TemplateView, FormView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages

from models import Grupo, Topico
from forms import AddTopicoForm, AddConversaForm



class ForumView(TemplateView):
    template_name = 'forum/forum.html'

    def get_context_data(self, **kwargs):
        context = super(ForumView, self).get_context_data(**kwargs)

        grupos_list = Grupo.objects.filter(grupousuario__usuario=self.request.user)
        paginator = Paginator(grupos_list, 10)

        page = self.request.GET.get('page')
        try:
            grupos = paginator.page(page)
        except PageNotAnInteger:
            grupos = paginator.page(1)
        except EmptyPage:
            grupos = paginator.page(paginator.num_pages)

        context['grupos'] = grupos
        return context


class GrupoView(DetailView):
    model = Grupo
    template_name = 'forum/grupo.html'

    def get_object(self, queryset=None):
        obj = super(GrupoView, self).get_object(queryset)
        if not obj.grupousuario_set.filter(usuario=self.request.user).exists():
            raise PermissionDenied()
        return obj

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
        return context


class TopicoAddView(FormView):
    template_name = 'forum/topico-add.html'
    form_class = AddTopicoForm

    def get_grupo(self):
        obj = get_object_or_404(Grupo, pk=self.kwargs['grupo_pk'])
        if not obj.grupousuario_set.filter(usuario=self.request.user).exists():
            raise PermissionDenied()
        return obj

    def form_valid(self, form):
        instance = form.save(grupo=self.get_grupo(), criador=self.request.user)
        messages.info(self.request, u'Tópico criado com sucesso!')
        return HttpResponseRedirect(instance.get_absolute_url())

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os campos!")
        return super(TopicoAddView, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(TopicoAddView, self).get_context_data(**kwargs)
        context['object'] = self.get_grupo()
        return context


class TopicoView(DetailView):
    model = Topico
    template_name = 'forum/topico.html'
    form_class = AddConversaForm

    def get(self, request, *args, **kwargs):
        self.form = self.form_class()
        return super(TopicoView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.form = self.form_class(request.POST, request.FILES)
        if self.form.is_valid():
            return self.form_valid(self.form)
        else:
            return self.form_invalid(self.form)

    def get_queryset(self):
        return super(TopicoView, self).get_queryset().filter(status='A')

    def get_object(self, queryset=None):
        obj = super(TopicoView, self).get_object(queryset)
        if not obj.grupo.grupousuario_set.filter(usuario=self.request.user).exists():
            raise PermissionDenied()
        return obj

    def form_valid(self, form):
        self.object = self.get_object()
        instance = form.save(topico=self.object, autor=self.request.user)
        self.form = self.form_class()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os campos!")
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(TopicoView, self).get_context_data(**kwargs)

        conversas_list = self.object.conversa_set.filter(conversa_pai=None)
        paginator = Paginator(conversas_list, 10)

        page = self.request.GET.get('page')
        try:
            conversas = paginator.page(page)
        except PageNotAnInteger:
            conversas = paginator.page(1)
        except EmptyPage:
            conversas = paginator.page(paginator.num_pages)

        context['form'] = self.form
        context['conversas'] = conversas
        return context