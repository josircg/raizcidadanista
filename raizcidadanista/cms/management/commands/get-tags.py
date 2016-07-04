#-*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand
from django.utils.html import strip_tags

from cms.models import Recurso, Article

from datetime import date, timedelta
from HTMLParser import HTMLParser
from collections import Counter
import string


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        recurso = Recurso.objects.get_or_create(recurso='TAGS')[0]
        recurso_exclude = Recurso.objects.get_or_create(recurso='TAGS-EXC')[0].valor.split(',')

        # Pegar todo o conteúdo publicado nos ultimos 7 dias
        #content = u''.join(list(Article.objects.active().filter(created_at__gte=date.today()+timedelta(days=7)).values_list('content', flat=True)))
        content = u''.join(list(Article.objects.active().values_list('content', flat=True)))
        # Remover as marcações HTML
        content = u'%s' % HTMLParser().unescape(strip_tags(content))
        # Remover caracteres de pontuação, espaçamento, preposições e artigos
        prepos = [u'’', u'‘', u'\'', u'”', u'“', u'"', u'\n', u'\t', u'\r',] + recurso_exclude + list(string.punctuation)
        for prepo in prepos:
            content = content.replace(prepo, u' ')
        # Separar palavras
        content_words = content.split(u' ')
        # Remover palavras com menos de 3 caracteres
        content_words = [word for word in content_words if len(word) > 3]
        #print content_words
        # Pegar as 30 mais usadas e salvar no recurso
        content_words_count = Counter(content_words).most_common(30)
        recurso.valor = content_words_count
        recurso.save()