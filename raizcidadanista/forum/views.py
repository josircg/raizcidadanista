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
from django.conf import settings

from models import Grupo, GrupoUsuario, Topico, Conversa, ConversaCurtida, STATUS_CURTIDA, LOCALIZACAO, \
    TopicoOuvinte, ConversaMencao, GrupoCategoria, Proposta, PropostaOpcao
from forms import AddEditTopicoForm, ConversaForm, PesquisaForm, GrupoForm, MencaoForm, AddMembrosForm, \
    AddPropostaForm, AddEnqueteForm, VotoPropostaForm, VotoEnqueteForm

from cms.email import sendmail

from datetime import datetime
import json


class ForumFilterView(TemplateView):
    template_name = 'forum/forum-filter.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('localizacao'):
            request.session['localizacao'] = request.POST.get('localizacao')
            return HttpResponseRedirect(reverse('forum_recentes'))
        return super(ForumFilterView, self).post(request, *args, **kwargs)


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
        grupos_queryset = Grupo.objects.filter(grupousuario__usuario=self.request.user)
        grupos_list = []
        for grupo in grupos_queryset:
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
        context['titulo'] = u'Tópicos recentes'
        # Filtro
        if self.request.session.get('localizacao'):
            if self.request.session.get('localizacao') == 'N':
                context['titulo'] += u' da Teia Nacional'
            elif self.request.session.get('localizacao') == 'E':
                context['titulo'] += u' da Teia Estadual'
            elif self.request.session.get('localizacao') == 'M':
                context['titulo'] += u' da Teia Municipal'

        # As Propostas em aberto que forem de escopo global ou se forem locais mas o usuário estiver inscrito no grupo, devem aparecer em destaque antes mesmo dos tópicos prioritários.
        context['propostas'] = Proposta.objects.filter(status='A', dt_encerramento__gte=datetime.now()).filter(Q(escopo='L') | Q(topico__grupo__grupousuario__usuario=self.request.user)).distinct()
        # Filtro
        if self.request.session.get('localizacao'):
            context['propostas'] = context['propostas'].filter(topico__grupo__localizacao=self.request.session.get('localizacao'))

        topicos_queryset = Topico.objects.filter(topicoouvinte__ouvinte=self.request.user).distinct()
        # Filtro
        if self.request.session.get('localizacao'):
            topicos_queryset = topicos_queryset.filter(grupo__localizacao=self.request.session.get('localizacao'))

        topicos_prioritarios_list = topicos_queryset.filter(topicoouvinte__notificacao='P').order_by('-dt_ultima_atualizacao')
        topicos_list = list(topicos_prioritarios_list)+list(topicos_queryset.exclude(topicoouvinte__notificacao='P').order_by('-dt_ultima_atualizacao'))
        paginator = Paginator(topicos_list, 10)

        page = self.request.GET.get('page')
        try:
            topicos = paginator.page(page)
        except PageNotAnInteger:
            topicos = paginator.page(1)
        except EmptyPage:
            topicos = paginator.page(paginator.num_pages)

        context['topicos'] = topicos

        # Filtro Estadual/Municial
        if self.request.session.get('localizacao') in ('E', 'M') and not Grupo.objects.filter(grupousuario__usuario=self.request.user, localizacao=self.request.session.get('localizacao')).exists():
            context['grupos'] = Grupo.objects.filter(localizacao=self.request.session.get('localizacao'))

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
        texto = form.cleaned_data.get('texto')
        listar_conversas = form.cleaned_data.get('listar_conversas')

        if listar_conversas:
            results_list = Conversa.objects.all()
            if autor:
                results_list = results_list.filter(autor__first_name__icontains=autor)
            if grupo:
                results_list = results_list.filter(topico__grupo__nome__icontains=grupo)
            if texto:
                results_list = results_list.filter(Q(topico__titulo__icontains=texto) | Q(texto__icontains=texto))
        else:
            results_list = Topico.objects.all()
            if autor:
                results_list = results_list.filter(conversa__autor__first_name__icontains=autor)
            if grupo:
                results_list = results_list.filter(grupo__nome__icontains=grupo)
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
                'listar_conversas': listar_conversas,
            }
        )

class GrupoView(DetailView):
    model = Grupo
    template_name = 'forum/grupo.html'

    def get_context_data(self, **kwargs):
        context = super(GrupoView, self).get_context_data(**kwargs)

        # A página do Grupo que tiver uma proposta aberta, deve mostrar um item com a proposta na primeira linha antes da listagem dos tópicos.
        context['propostas'] = Proposta.objects.filter(topico__grupo=self.object, status='A', dt_encerramento__gte=datetime.now())

        topicos_list = self.object.topico_set.all()
        if self.request.GET.get('categoria'):
            context['categoria'] = get_object_or_404(GrupoCategoria, pk=self.request.GET.get('categoria'))
            topicos_list = topicos_list.filter(categoria=context['categoria'])
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
    formset_class = inlineformset_factory(Grupo, GrupoCategoria, fields=('descricao', ), extra=3, can_delete=False)

    def get_object(self, queryset=None):
        obj = super(GrupoEditView, self).get_object(queryset)
        if not self.request.user.is_superuser and not obj.grupousuario_set.filter(usuario=self.request.user, admin=True).exists():
            raise PermissionDenied()
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = self.formset_class(instance=self.object, queryset=self.object.grupocategoria_set.all())
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = self.formset_class(request.POST, instance=self.object)

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_invalid(self, form, formset):
        return self.render_to_response(
            self.get_context_data(
                form=form,
                formset=formset,
                object=self.object
            )
        )

    def form_valid(self, form, formset):
        messages.info(self.request, u'Grupo salvo com sucesso!')
        form.save()
        formset.save()
        formset = self.formset_class(instance=self.object)
        return HttpResponseRedirect(reverse('forum_grupo_edit', kwargs={'pk': self.object.pk, }))


class GrupoEditMembrosView(DetailView):
    template_name = 'forum/grupo-edit-membros.html'
    model = Grupo
    formset_class = inlineformset_factory(Grupo, GrupoUsuario, fields=('admin', ), extra=0)

    def get_object(self, queryset=None):
        obj = super(GrupoEditMembrosView, self).get_object(queryset)
        if not self.request.user.is_superuser and not obj.grupousuario_set.filter(usuario=self.request.user, admin=True).exists():
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


class GrupoAddMembrosView(FormView):
    template_name = 'forum/grupo-add-membros.html'
    form_class = AddMembrosForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.GET.get('q'):
            # List of users
            json_response = []
            queryset = User.objects.exclude(
                pk__in=self.object.grupousuario_set.values_list('usuario', flat=True)
            ).filter(
                Q(first_name__icontains=request.GET.get('q')) | Q(username__icontains=request.GET.get('q'))
            )
            for user in queryset:
                json_response.append({
                  'id': user.pk,
                  'name': u'%s' % user,
                })
            return HttpResponse(json.dumps(json_response), mimetype='application/json')
        return super(GrupoAddMembrosView, self).get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = get_object_or_404(Grupo, pk=self.kwargs['pk'])
        if not self.request.user.is_superuser and not obj.grupousuario_set.filter(usuario=self.request.user, admin=True).exists():
            raise PermissionDenied()
        return obj

    def get_form_kwargs(self):
        kwargs = super(GrupoAddMembrosView, self).get_form_kwargs()
        kwargs['grupo'] = self.get_object()
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os campos!")
        self.object = self.get_object()
        context = self.get_context_data(object=self.object, form=form)
        return self.render_to_response(context)

    def form_valid(self, form):
        form.save()
        messages.info(self.request, u'Membros adicionados com sucesso!')
        return HttpResponseRedirect(reverse('forum_grupo_add_membros', kwargs={'pk': self.get_object().pk, }))

    def get_context_data(self, **kwargs):
        context = super(GrupoAddMembrosView, self).get_context_data(**kwargs)
        context['object'] = self.get_object()
        return context


class TopicoAddView(FormView):
    template_name = 'forum/topico-add.html'
    form_class = AddEditTopicoForm

    def get_grupo(self):
        return get_object_or_404(Grupo, pk=self.kwargs['grupo_pk'])

    def get(self, request, *args, **kwargs):
        self.grupo = self.get_grupo()
        if not self.grupo.grupousuario_set.filter(usuario=request.user).exists() and self.grupo.privado:
            messages.error(request, u'Este grupo é privado e só permite a inclusão de novos tópicos pelos membros previamente aprovados. <a href="%s">Clique aqui</a> para solicitar o seu ingresso nesse grupo.' % (
                reverse('forum_grupo_solicitar_ingresso', kwargs={'pk': self.grupo.pk, })
            ))
            return HttpResponseRedirect(self.grupo.get_absolute_url())
        return super(TopicoAddView, self).get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(TopicoAddView, self).get_form_kwargs()
        kwargs['grupo'] = self.get_grupo()
        return kwargs

    def form_valid(self, form):
        instance = form.save(grupo=self.get_grupo(), criador=self.request.user)
        messages.info(self.request, u'Tópico criado com sucesso!')
        return HttpResponseRedirect(instance.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super(TopicoAddView, self).get_context_data(**kwargs)
        context['object'] = self.get_grupo()
        return context


class TopicoEditView(FormView):
    template_name = 'forum/topico-edit.html'
    form_class = AddEditTopicoForm

    def get_grupo(self):
        return get_object_or_404(Grupo, pk=self.kwargs['grupo_pk'])

    def get_instance(self):
        return get_object_or_404(Topico, pk=self.kwargs['pk'])

    def get(self, request, pk, *args, **kwargs):
        self.grupo = self.get_grupo()
        self.instance = self.get_instance()
        if self.instance.criador == request.user or request.user.is_superuser or self.grupo.grupousuario_set.filter(usuario=request.user, admin=True).exists():
            return super(TopicoEditView, self).get(request, *args, **kwargs)
        else:
            messages.error(request, u'A edição de um tópico só pode ser feita pelo seu criador.')
            return HttpResponseRedirect(self.instance.get_absolute_url())

    def post(self, request, pk, *args, **kwargs):
        self.grupo = self.get_grupo()
        self.instance = self.get_instance()

        if self.instance.criador == request.user or request.user.is_superuser or self.grupo.grupousuario_set.filter(usuario=request.user, admin=True).exists():
            return super(TopicoEditView, self).post(request, *args, **kwargs)
        else:
            messages.error(request, u'A edição de um tópico só pode ser feita pelo seu criador.')
            return HttpResponseRedirect(self.instance.get_absolute_url())

    def get_form_kwargs(self):
        kwargs = super(TopicoEditView, self).get_form_kwargs()
        kwargs['grupo'] = self.grupo
        kwargs['instance'] = self.instance
        return kwargs

    def form_valid(self, form):
        instance = form.save(grupo=self.grupo, criador=self.request.user)
        messages.info(self.request, u'Tópico criado com sucesso!')
        return HttpResponseRedirect(instance.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super(TopicoEditView, self).get_context_data(**kwargs)
        context['grupo'] = self.grupo
        context['object'] = self.instance
        return context


class SaidaGrupoView(DetailView):
    model = Grupo

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        GrupoUsuario.objects.filter(
            grupo=self.object,
            usuario=request.user,
        ).delete()
        messages.info(request, u'Você foi removido do grupo %s!' % self.object)
        return HttpResponseRedirect(self.object.get_absolute_url())


class SolicitarIngressoView(DetailView):
    model = Grupo

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.privado:
            sendmail(
                subject=u'Solicitação de ingresso no grupo %s' % self.object,
                to=list(self.object.grupousuario_set.filter(admin=True).values_list(u'usuario__email', flat=True)),
                template='forum/emails/solicitacao-ingresso.html',
                params={
                    'grupo': self.object,
                    'usuario': request.user,
                    'host': settings.SITE_HOST,
                },
            )
            messages.info(request, u'O seu ingresso neste grupo foi solicitado. Assim que aprovado, você será incluído como membro deste. Obrigado!')
        else:
            GrupoUsuario(
                grupo=self.object,
                usuario=request.user,
            ).save()
            messages.info(request, u'Seja bem vindo ao grupo %s!' % self.object)
        return HttpResponseRedirect(self.object.get_absolute_url())


class SolicitarIngressoAprovarView(DetailView):
    model = Grupo

    def get_user(self):
        return get_object_or_404(User, pk=self.kwargs['user_pk'])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.user = self.get_user()
        if not self.object.grupousuario_set.filter(usuario=request.user, admin=True).exists():
            messages.error(request, u'Você não tem permissão para aprovar novos membros!')
            return HttpResponseRedirect(self.object.get_absolute_url())

        GrupoUsuario(
            grupo=self.object,
            usuario=self.user,
        ).save()
        messages.info(request, u'Usuários %s incluido com sucesso nesse grupo.' % self.user)
        return HttpResponseRedirect(self.object.get_absolute_url())


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
            if self.object.criador == request.user or self.object.grupo.grupousuario_set.filter(usuario=request.user, admin=True).exists():
                self.object.status = 'F'
                self.object.save()
                Conversa(
                    topico=self.object,
                    autor=request.user,
                    texto=u'Tópico encerrado.'
                ).save()
                messages.info(request, u'Tópico encerrado!')
                return HttpResponseRedirect(self.object.get_absolute_url())
            else:
                raise PermissionDenied

        # Reabrir Tópico
        if request.GET.get('reabrir'):
            if self.object.criador == request.user or self.object.grupo.grupousuario_set.filter(usuario=request.user, admin=True).exists():
                self.object.status = 'A'
                self.object.save()
                Conversa(
                    topico=self.object,
                    autor=request.user,
                    texto=u'Tópico reaberto.'
                ).save()
                messages.info(request, u'Tópico reaberto!')
                return HttpResponseRedirect(self.object.get_absolute_url())
            else:
                raise PermissionDenied

        # Alterar o tipo de notificação
        if request.GET.get('notificacao'):
            try:
                ouvinte = TopicoOuvinte.objects.filter(topico=self.object, ouvinte=self.request.user).latest('pk')
            except TopicoOuvinte.DoesNotExist:
                ouvinte = TopicoOuvinte.objects.create(topico=self.object, ouvinte=self.request.user)
            ouvinte.notificacao = request.GET.get('notificacao')
            ouvinte.save()
            messages.info(request, u'Notificações alterada para: %s.' % ouvinte.get_notificacao_display())
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
        # A proposta tem que aparecer sempre no timeline do tópico: se já tiver concluída, mostrar pela ordenação da data.
        conversas_list = conversas_list.filter(Q(proposta=None) | Q(proposta__status='F') | Q(proposta__dt_encerramento__lt=datetime.now())).distinct()
        # Se estiver em aberto, mostrar no topo do tópico.
        context['propostas'] = self.object.conversa_set.filter(proposta__status='A', proposta__dt_encerramento__gte=datetime.now())

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
        try:
            context['ouvinte'] = TopicoOuvinte.objects.filter(topico=self.object, ouvinte=self.request.user).latest('pk')
        except TopicoOuvinte.DoesNotExist:
            context['ouvinte'] = TopicoOuvinte.objects.create(topico=self.object, ouvinte=self.request.user)
        return context


class NotificarTopicoView(DetailView):
    model = Topico

    def get(self, request, *args, **kwargs):
        def splip_emails(emails, ite=50):
                ini = 0
                for i in range(ite, len(emails), ite):
                    yield emails[ini:i]
                    ini = i
                if len(emails) > ini:
                    yield emails[ini:len(emails)]

        self.object = self.get_object()
        if request.user.is_superuser or self.object.grupo.grupousuario_set.filter(usuario=request.user, admin=True).exists():
            emails_list = TopicoOuvinte.objects.filter(topico__grupo=self.object.grupo).values_list('ouvinte__email', flat=True).distinct()
            for emails in splip_emails(emails_list):
                sendmail(
                    subject=self.object.titulo,
                    bcc=emails,
                    template='forum/emails/notificacao-topico.html',
                    params={
                        'topico': self.object,
                        'host': settings.SITE_HOST,
                    },
                )
            messages.info(request, u'Notificação enviada com sucesso!')
            return HttpResponseRedirect(self.object.get_absolute_url())
        raise PermissionDenied()


class MencaoView(FormView):
    form_class = MencaoForm

    def get(self, request, *args, **kwargs):
        # List of users
        json_response = []
        for user in User.objects.all():
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
            if not ConversaMencao.objects.filter(conversa=form.cleaned_data.get('conversa'), mencao=mencao).exists():
                ConversaMencao(conversa=form.cleaned_data.get('conversa'), mencao=mencao, colaborador=self.request.user).save()
                messages.info(self.request, u'Menção realizada com sucesso!')
            else:
                messages.error(self.request, u"%s já foi mencionado anteriormente!" % mencao)
        return HttpResponseRedirect(form.cleaned_data.get('conversa').get_absolute_url())

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os campos!")
        return HttpResponseRedirect(form.instance.conversa.get_absolute_url())


class NovaPropostaTopicoView(FormView):
    template_name = 'forum/topico-add-proposta.html'
    form_class = AddPropostaForm

    def get_topico(self):
        return get_object_or_404(Topico, pk=self.kwargs['pk'])

    def get_grupo(self):
        return get_object_or_404(Grupo, pk=self.kwargs['grupo_pk'])

    def get(self, request, *args, **kwargs):
        self.grupo = self.get_grupo()
        if not self.grupo.grupousuario_set.filter(usuario=request.user).exists() and self.grupo.privado:
            messages.error(request, u'Este grupo é privado e só permite a inclusão de novas propostas pelos membros previamente aprovados. <a href="%s">Clique aqui</a> para solicitar o seu ingresso nesse grupo.' % (
                reverse('forum_grupo_solicitar_ingresso', kwargs={'pk': self.grupo.pk, })
            ))
            return HttpResponseRedirect(self.grupo.get_absolute_url())
        return super(NovaPropostaTopicoView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        instance = form.save(topico=self.get_topico(), autor=self.request.user)
        messages.info(self.request, u'Proposta publicada com sucesso!')
        return HttpResponseRedirect(instance.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super(NovaPropostaTopicoView, self).get_context_data(**kwargs)
        context['object'] = self.get_topico()
        return context


class PropostaTopicoView(FormView):
    model = Proposta
    template_name = 'forum/topico-proposta.html'
    form_class = VotoPropostaForm

    def get_object(self):
        return get_object_or_404(Proposta, pk=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(PropostaTopicoView, self).post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.GET.get('encerrar') and (request.user.is_superuser or self.object.autor == request.user or self.object.topico.grupo.grupousuario_set.filter(usuario=request.user, admin=True).exists()):
            self.object.status = 'F'
            self.object.save()
            return HttpResponseRedirect(self.object.get_absolute_url())
        if request.GET.get('reabrir') and (request.user.is_superuser or self.object.autor == request.user or self.object.topico.grupo.grupousuario_set.filter(usuario=request.user, admin=True).exists()):
            self.object.status = 'A'
            self.object.save()
            messages.info(request, u'Proposta Reaberta!')
            return HttpResponseRedirect(self.object.get_absolute_url())
        return super(PropostaTopicoView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        form.save(proposta=self.object, eleitor=self.request.user)
        messages.info(self.request, u'Obrigado pela sua opinião!')
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super(PropostaTopicoView, self).get_context_data(**kwargs)
        context['object'] = self.object
        try: context['respondido'] = self.object.voto_set.filter(eleitor=self.request.user).latest('pk')
        except: pass
        context['respondido_percent'] = (float(self.object.voto_set.count())/float((self.object.topico.topicoouvinte_set.count() or 1)))*100
        context['finalizado'] = self.object.status == 'F' or self.object.dt_encerramento < datetime.now()
        if context['finalizado']:
            messages.warning(self.request, u'Proposta Encerrada!')

        context['respostas'] = [
            ['Concordar', self.object.voto_set.filter(voto='C').count()],
            ['Abster', self.object.voto_set.filter(voto='A').count()],
            ['Discordar', self.object.voto_set.filter(voto='D').count()],
            ['Vetar', self.object.voto_set.filter(voto='V').count()],
        ]
        return context


class NovaEnqueteTopicoView(FormView):
    template_name = 'forum/topico-add-enquete.html'
    form_class = AddEnqueteForm
    formset_class = inlineformset_factory(Proposta, PropostaOpcao, fields=('opcao', ), extra=5, can_delete=False)

    def get_topico(self):
        return get_object_or_404(Topico, pk=self.kwargs['pk'])

    def get_grupo(self):
        return get_object_or_404(Grupo, pk=self.kwargs['grupo_pk'])

    def get(self, request, *args, **kwargs):
        self.grupo = self.get_grupo()
        if not self.grupo.grupousuario_set.filter(usuario=request.user).exists() and self.grupo.privado:
            messages.error(request, u'Este grupo é privado e só permite a inclusão de novas enquetes pelos membros previamente aprovados. <a href="%s">Clique aqui</a> para solicitar o seu ingresso nesse grupo.' % (
                reverse('forum_grupo_solicitar_ingresso', kwargs={'pk': self.grupo.pk, })
            ))
            return HttpResponseRedirect(self.grupo.get_absolute_url())
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = self.formset_class()
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = self.formset_class(request.POST)

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_invalid(self, form, formset):
        return self.render_to_response(
            self.get_context_data(
                form=form,
                formset=formset
            )
        )

    def form_valid(self, form, formset):
        instance = form.save(topico=self.get_topico(), autor=self.request.user)
        formset.instance = instance
        formset.save()
        messages.info(self.request, u'Enquete publicada com sucesso!')
        return HttpResponseRedirect(instance.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super(NovaEnqueteTopicoView, self).get_context_data(**kwargs)
        context['object'] = self.get_topico()
        return context


class EnqueteTopicoView(FormView):
    model = Proposta
    template_name = 'forum/topico-enquete.html'
    form_class = VotoEnqueteForm

    def get_object(self):
        return get_object_or_404(Proposta, pk=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(EnqueteTopicoView, self).post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.GET.get('encerrar') and (self.object.autor == request.user or self.object.topico.grupo.GrupoUsuario_set.filter(usuario=request.user, admin=True).exists()):
            self.object.status = 'F'
            self.object.save()
            return HttpResponseRedirect(self.object.get_absolute_url())
        if request.GET.get('reabrir') and (self.object.autor == request.user or self.object.topico.grupo.GrupoUsuario_set.filter(usuario=request.user, admin=True).exists()):
            self.object.status = 'A'
            self.object.save()
            messages.info(request, u'Enquete Reaberta!')
            return HttpResponseRedirect(self.object.get_absolute_url())
        return super(EnqueteTopicoView, self).get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(EnqueteTopicoView, self).get_form_kwargs()
        kwargs['proposta'] = self.get_object()
        return kwargs

    def form_valid(self, form):
        form.save(proposta=self.object, eleitor=self.request.user)
        messages.info(self.request, u'Obrigado pela sua opinião!')
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super(EnqueteTopicoView, self).get_context_data(**kwargs)
        context['object'] = self.object
        try: context['respondido'] = self.object.voto_set.filter(eleitor=self.request.user).latest('pk')
        except: pass
        context['respondido_percent'] = (float(self.object.voto_set.count())/float((self.object.topico.topicoouvinte_set.count() or 1)))*100
        context['finalizado'] = self.object.status == 'F' or self.object.dt_encerramento < datetime.now()
        if context['finalizado']:
            messages.warning(self.request, u'Enquete Encerrada!')

        context['respostas'] = []
        for opcao in self.object.propostaopcao_set.all():
            context['respostas'].append((u'%s' % opcao, opcao.voto_set.count()))
        return context