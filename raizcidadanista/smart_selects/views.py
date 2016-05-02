import locale

from django.db.models import get_model
from django.http import HttpResponse
import json as simplejson
from django.contrib.auth.decorators import login_required

from smart_selects.utils import unicode_sorter


@login_required(login_url='/')
def filterchain(request, app, model, manager=None):
    model_class = get_model(app, model)
    keywords = {}
    for field, value in request.GET.items():
        if value == '0':
            keywords[str("%s__isnull" % field)] = True
        elif value:
            keywords[str(field)] = str(value) or None

    if manager is not None and hasattr(model_class, manager):
        queryset = getattr(model_class, manager)
    else:
        queryset = model_class._default_manager

    results = queryset.filter(**keywords)
    if not len(keywords):
        results = results.none()

    if not getattr(model_class._meta, 'ordering', False):
        results = list(results)
        results.sort(cmp=locale.strcoll, key=lambda x: unicode_sorter(unicode(x)))

    result = []
    for item in results:
        result.append({'value': item.pk, 'display': unicode(item)})
    json = simplejson.dumps(result)
    return HttpResponse(json, content_type='application/json')


@login_required(login_url='/')
def filterchain_all(request, app, model):
    model_class = get_model(app, model)
    keywords = {}
    for field, value in request.GET.items():
        if value == '0':
            keywords[str("%s__isnull" % field)] = True
        elif value:
            keywords[str(field)] = str(value) or None

    queryset = model_class._default_manager.filter(**keywords)
    if not len(keywords):
        queryset = queryset.none()

    results = list(queryset)
    results.sort(cmp=locale.strcoll, key=lambda x: unicode_sorter(unicode(x)))
    final = []
    for item in results:
        final.append({'value': item.pk, 'display': unicode(item)})
    results = list(model_class._default_manager.exclude(**keywords))
    results.sort(cmp=locale.strcoll, key=lambda x: unicode_sorter(unicode(x)))
    final.append({'value': "", 'display': "---------"})

    for item in results:
        final.append({'value': item.pk, 'display': unicode(item)})
    json = simplejson.dumps(final)
    return HttpResponse(json, content_type='application/json')
