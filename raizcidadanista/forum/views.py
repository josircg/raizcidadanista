# -*- coding: utf-8 -*-
from django.views.generic import DetailView, TemplateView, FormView, UpdateView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User

from models import Grupo, GrupoUsuario, Topico, Conversa, ConversaCurtida, STATUS_CURTIDA, LOCALIZACAO, TopicoOuvinte, ConversaMencao
from forms import AddTopicoForm, ConversaForm, PesquisaForm, GrupoForm, MencaoForm

from datetime import datetime
import json


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


class DiretorioView(TemplateView):
    template_name = 'forum/diretorio.html'

    def get_context_data(self, **kwargs):
        context = super(DiretorioView, self).get_context_data(**kwargs)

        grupos_list = Grupo.objects.all()

        if self.request.GET.get('grupo'):
            grupos_list = grupos_list.filter(nome__icontains=self.request.GET.get('grupo'))
            context['grupo'] = self.request.GET.get('grupo')

        if self.request.GET.get('localizacao'):
            grupos_list = grupos_list.filter(localizacao=self.request.GET.get('localizacao'))
            context['localizacao'] = self.request.GET.get('localizacao')

        if self.request.GET.get('tematico'):
            grupos_list = grupos_list.filter(tematico=True if self.request.GET.get('tematico') == 'true' else False)
            context['tematico'] = self.request.GET.get('tematico')

        paginator = Paginator(grupos_list, 10)

        page = self.request.GET.get('page')
        try:
            grupos = paginator.page(page)
        except PageNotAnInteger:
            grupos = paginator.page(1)
        except EmptyPage:
            grupos = paginator.page(paginator.num_pages)

        context['grupos'] = grupos
        context['localizacao_choices'] = LOCALIZACAO
        return context


class NaoLidosView(TemplateView):
    template_name = 'forum/nao-lidos.html'

    def get_context_data(self, **kwargs):
        context = super(NaoLidosView, self).get_context_data(**kwargs)

        grupos_list = []
        for grupo in Grupo.objects.filter(grupousuario__usuario=self.request.user):
            if grupo.num_topicos_nao_lidos(self.request.user) > 0:
                grupos_list.append(grupo)
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


class RecentesView(TemplateView):
    template_name = 'forum/recentes.html'

    def get_context_data(self, **kwargs):
        context = super(RecentesView, self).get_context_data(**kwargs)

        topicos_list = Topico.objects.filter(topicoouvinte__ouvinte=self.request.user).order_by('-dt_ultima_atualizacao')
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


class MeuPerfilView(TemplateView):
    template_name = 'forum/meu-perfil.html'

    def get(self, request, *args, **kwargs):
        if not request.user.membro.exists():
            messages.error(request, u'Não há nenhum Membro associado a esse usuário!')
            return HttpResponseRedirect(reverse('forum'))
        return super(MeuPerfilView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MeuPerfilView, self).get_context_data(**kwargs)
        context['membro'] = self.request.user.membro.all()[0]
        return context


class PesquisaView(FormView):
    template_name = 'forum/pesquisa.html'
    form_class = PesquisaForm

    def get(self, request, *args, **kwargs):
        # Permitir GET and POST
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if request.GET.get('texto') != None or request.GET.get('autor') != None or request.GET.get('grupo') != None:
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def get_form_kwargs(self):
        kwargs = super(PesquisaView, self).get_form_kwargs()
        if self.request.GET.get('texto') != None or self.request.GET.get('autor') != None or self.request.GET.get('grupo') != None:
            kwargs['data'] = self.request.GET.copy()
        return kwargs

    def form_valid(self, form):
        autor = form.cleaned_data.get('autor')
        grupo = form.cleaned_data.get('grupo')

        results_list = Topico.objects.all()
        if autor:
            results_list = results_list.filter(conversa__autor__first_name__icontains=autor)
        if grupo:
            results_list = results_list.filter(grupo__nome__icontains=grupo)
        texto = form.cleaned_data.get('texto')
        if texto:
            results_list = results_list.filter(Q(titulo__icontains=texto) | Q(conversa__texto__icontains=texto))

        results_list = results_list.distinct()

        paginator = Paginator(results_list, 10)

        page = self.request.GET.get('page')
        try:
            results = paginator.page(page)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(paginator.num_pages)

        return self.response_class(
            request=self.request,
            template=self.template_name,
            context={
                'results': results,
                'form': form,
            }
        )

class GrupoView(DetailView):
    model = Grupo
    template_name = 'forum/grupo.html'

    def get_context_data(self, **kwargs):
        context = super(GrupoView, self).get_context_data(**kwargs)

        topicos_list = self.object.topico_set.all()
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


class GrupoEditView(UpdateView):
    template_name = 'forum/grupo-edit.html'
    model = Grupo
    form_class = GrupoForm

    def get_object(self, queryset=None):
        obj = super(GrupoEditView, self).get_object(queryset)
        if not obj.grupousuario_set.filter(usuario=self.request.user, admin=True).exists():
            raise PermissionDenied()
        return obj

    def form_valid(self, form):
        messages.info(self.request, u'Grupo salvo com sucesso!')
        return super(GrupoEditView, self).form_valid(form)


class GrupoEditMembrosView(DetailView):
    template_name = 'forum/grupo-edit-membros.html'
    model = Grupo
    formset_class = inlineformset_factory(Grupo, GrupoUsuario, fields=('admin', ), extra=0)

    def get_object(self, queryset=None):
        obj = super(GrupoEditMembrosView, self).get_object(queryset)
        if not obj.grupousuario_set.filter(usuario=self.request.user, admin=True).exists():
            raise PermissionDenied()
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Paginação do formset
        queryset_list = self.object.grupousuario_set.all()
        if request.GET.get('q'):
            queryset_list = queryset_list.filter(Q(usuario__first_name__icontains=request.GET.get('q')) | Q(usuario__username__icontains=request.GET.get('q'))).distinct()
        paginator = Paginator(queryset_list, 50)
        page = request.GET.get('page')
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)
        page_queryset = queryset_list.filter(id__in=[object.pk for object in objects])

        formset = self.formset_class(instance=self.object, queryset=page_queryset)
        return self.render_to_response(
            self.get_context_data(
                formset=formset,
                object=self.object,
                objects=objects,
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = self.formset_class(request.POST, instance=self.object)
        if formset.is_valid():
            return self.form_valid(formset)
        else:
            return self.form_invalid(formset)

    def form_valid(self, formset):
        formset.save()
        messages.info(self.request, u'Membros editados com sucesso!')
        formset = self.formset_class(instance=self.object)
        return HttpResponseRedirect(reverse('forum_grupo_edit_membros', kwargs={'pk': self.object.pk, }))

    def form_invalid(self, formset):
        return self.render_to_response(
            self.get_context_data(
                formset=formset,
                object=self.object
            )
        )


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

    def get_context_data(self, **kwargs):
        context = super(TopicoAddView, self).get_context_data(**kwargs)
        context['object'] = self.get_grupo()
        return context


class TopicoView(DetailView):
    model = Topico
    template_name = 'forum/topico.html'
    form_class = ConversaForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Excluir conversa
        if request.GET.get('conversa') and request.GET.get('excluir'):
            conversa = get_object_or_404(Conversa, pk=request.GET.get('conversa'), autor=request.user)
            if not conversa.has_delete(request.user):
                raise Http404
            conversa.delete()
            messages.info(request, u'Comentário removido com sucesso!')
            return HttpResponseRedirect(self.object.get_absolute_url())

        # Encerrar Tópico
        if request.GET.get('encerrar'):
            if self.object.criador != request.user:
                raise PermissionDenied
            self.object.status = 'F'
            self.object.save()
            messages.info(request, u'Tópico encesstado!')
            return HttpResponseRedirect(self.object.get_absolute_url())

        # Reabrir Tópico
        if request.GET.get('reabrir'):
            if self.object.criador != request.user:
                raise PermissionDenied
            self.object.status = 'A'
            self.object.save()
            messages.info(request, u'Tópico reaberto!')
            return HttpResponseRedirect(self.object.get_absolute_url())

        if request.is_ajax():
            # Computar curtidas
            if request.GET.get('conversa') and request.GET.get('curtir'):
                conversa = get_object_or_404(Conversa, pk=request.GET.get('conversa'))
                try:
                    cc = ConversaCurtida.objects.get(conversa=conversa, colaborador=request.user)
                except ConversaCurtida.DoesNotExist:
                    cc = ConversaCurtida(conversa=conversa, colaborador=request.user)

                # Descurtir
                if cc.curtida == request.GET.get('curtir'):
                    cc.delete()
                # Curtir
                else:
                    if request.GET.get('curtir') in ('I', 'C', 'P', 'N', ):
                        cc.curtida = request.GET.get('curtir')
                    cc.save()

                json_response = []
                for status, display in STATUS_CURTIDA:
                    json_response.append({
                        'status': status,
                        'count': conversa.conversacurtida_set.filter(curtida=status).count(),
                    })
                return HttpResponse(json.dumps(json_response), mimetype='application/json')

            # Ajax get likes
            if request.GET.get('conversa') and request.GET.get('get-curtir'):
                conversa = get_object_or_404(Conversa, pk=request.GET.get('conversa'))
                people = []
                curtidas = conversa.conversacurtida_set.filter(curtida=request.GET.get('get-curtir'))
                for curtida in curtidas[:15]:
                    people.append(u'%s' % curtida.colaborador.get_first_name())
                if curtidas.count() > 15:
                    people.append(u'e mais %s...' % (curtidas.count()-15))
                json_response= {
                    'status': request.GET.get('get-curtir'),
                    'people': people,
                    'count': curtidas.count(),
                }
                return HttpResponse(json.dumps(json_response), mimetype='application/json')
            # Ajax get mencao
            if request.GET.get('conversa') and request.GET.get('get-mencao'):
                conversa = get_object_or_404(Conversa, pk=request.GET.get('conversa'))
                people = []
                mencoes = conversa.conversamencao_set.all()
                for mencao in mencoes[:15]:
                    people.append(u'%s' % mencao.mencao.get_first_name())
                if mencoes.count() > 15:
                    people.append(u'e mais %s...' % (mencoes.count()-15))
                json_response= {
                    'people': people,
                    'count': mencoes.count(),
                }
                return HttpResponse(json.dumps(json_response), mimetype='application/json')
        self.form = self.form_class()
        return super(TopicoView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.form = self.form_class(request.POST, request.FILES)
        if request.POST.get('conversa'):
            instance = get_object_or_404(Conversa, pk=request.POST.get('conversa'))
            self.form = self.form_class(request.POST, request.FILES, instance=instance)
        if self.form.is_valid():
            return self.form_valid(self.form)
        else:
            return self.form_invalid(self.form)

    def get_object(self, queryset=None):
        obj = super(TopicoView, self).get_object(queryset)
        # Atualiza o número de conversas lidas
        obj.topicoouvinte_set.filter(ouvinte=self.request.user).update(dtleitura=datetime.now())
        return obj

    def form_valid(self, form):
        self.object = self.get_object()
        instance = form.save(topico=self.object, autor=self.request.user)
        return HttpResponseRedirect(instance.get_absolute_url())

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


class MencaoView(FormView):
    form_class = MencaoForm

    def get(self, request, *args, **kwargs):
        # List of users
        json_response = []
        for user in User.objects.filter(pk__in=TopicoOuvinte.objects.values_list('ouvinte', flat=True)).distinct():
            json_response.append({
              'id': user.pk,
              'name': u'%s' % user,
              'avatar': '',
              'icon': 'icon-16 icon-person',
              'type': 'contact'
            })
        return HttpResponse(json.dumps(json_response), mimetype='application/json')

    def form_valid(self, form):
        for mencao in form.cleaned_data.get('mencoes'):
            ConversaMencao(conversa=form.cleaned_data.get('conversa'), mencao=mencao, colaborador=self.request.user).save()
        messages.info(self.request, u'Menção realizada com sucesso!')
        return HttpResponseRedirect(form.cleaned_data.get('conversa').get_absolute_url())

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os campos!")
        return HttpResponseRedirect(form.instance.conversa.get_absolute_url())