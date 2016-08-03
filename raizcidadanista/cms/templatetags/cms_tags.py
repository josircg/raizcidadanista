# coding: utf-8
from django import template
from cms.models import Section, Article, ArticleComment, Recurso

from django.conf import settings
import re, random


register = template.Library()


@register.assignment_tag(takes_context=True)
def get_section(context, slug):
    try:
        section = Section.objects.get(slug=slug)
        if section.have_perm(context.get('request').user):
            return section
    except Section.DoesNotExist: pass
    return None


@register.assignment_tag(takes_context=True)
def get_article(context, slug):
    try:
        article = Article.objects.get(slug=slug)
        if article.have_perm(context.get('request').user):
            return article
    except Article.DoesNotExist: pass

    return None


@register.assignment_tag(takes_context=True)
def get_section_articles(context, slug, num=5):
    articles = []
    try:
        section = Section.objects.get(slug=slug)
        for article in section.get_articles():
            if article.have_perm(context.get('request').user):
                articles.append(article)
            if len(articles) == num: break
        return articles
    except Section.DoesNotExist:
        return []


@register.assignment_tag(takes_context=True)
def get_last_comments(context, num=5):
    return ArticleComment.objects.filter(active=True).order_by('-created_at')[:num]


@register.assignment_tag(takes_context=True)
def get_sections(context):
    sections = []
    for section in Section.objects.exclude(order=0):
        if section.have_perm(context.get('request').user) and section.num_articles() > 0:
            sections.append(section)
    return sections


@register.assignment_tag(takes_context=True)
def get_last_articles(context, num=10):
    articles = []
    for article in Article.objects.filter(is_active=True).order_by('sectionitem__order', '-created_at', '-pk')[:num]:
        if article.have_perm(context.get('request').user):
            articles.append(article)
    return articles


@register.simple_tag
def site_name():
    try:
        return Recurso.objects.get(recurso='SITE_NAME').valor
    except Recurso.DoesNotExist:
        return settings.SITE_NAME


@register.assignment_tag
def get_signup():
    try:
        return Recurso.objects.get(recurso='SIGNUP').ativo
    except Recurso.DoesNotExist:
        return False


@register.simple_tag
def version():
    return settings.VERSION


@register.simple_tag
def comment_title(article):
    if article.allow_comments == 'P':
        try:
            return Recurso.objects.get(recurso='COMMENT_P').valor
        except Recurso.DoesNotExist: return u'Faça um contato conosco'
    else:
        try:
            return Recurso.objects.get(recurso='COMMENT').valor
        except Recurso.DoesNotExist: return u'Adicione um comentário'


@register.assignment_tag(takes_context=True)
def get_cloudtags(context):
    try:
        tags_valor = dict(eval(Recurso.objects.get(recurso='TAGS').valor))
        maior_valor = max(tags_valor.values())
        tags = []
        for tag, num in tags_valor.items():
            tags.append((tag, (float(num)/float(maior_valor))*3.5))
        return tags
    except:
        return []


@register.assignment_tag(takes_context=True)
def get_items(context, section, query_param):
    request = context.get('request')
    query = request.GET.get(query_param)

    if section.link:
        raw_items = section.get_link_items(query=query)
        items = []
        for item in raw_items:
            items.append({
                'is_dataset': True,
                'url': item.get('url'),
                'title': item.get('descricao'),
            })
    else:
        raw_items = section.get_articles(query=query)
        items = []
        for item in raw_items:
            items.append({
                'is_dataset': False,
                'url': item.get_absolute_url(),
                'title': item.title,
            })

    return items


@register.tag(name='cleanwhitespace')
def do_cleanwhitespace(parser, token):
    nodelist = parser.parse(('endcleanwhitespace',))
    parser.delete_first_token()
    return CleanWhitespaceNode(nodelist)


class CleanWhitespaceNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        output = re.sub(r'\n[\s\t]*(?=\n)', '', output)
        output = re.sub(r'[\s\t]{2,}', '', output)
        output = output.strip()
        return output