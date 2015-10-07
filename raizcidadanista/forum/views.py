# -*- coding: utf-8 -*-
from django.views.generic import DetailView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from models import Grupo, Topico



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