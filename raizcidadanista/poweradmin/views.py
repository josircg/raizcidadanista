# -*- coding: utf-8 -*-
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import quote, get_fields_from_path
from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured
from django.core.paginator import InvalidPage
from django.db import models
from django.utils.encoding import force_unicode, smart_str
from django.utils.translation import ugettext, ugettext_lazy
from django.utils.http import urlencode
import operator

from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.util import (quote, get_fields_from_path,
    lookup_needs_distinct, prepare_lookup_value)

from datetime import datetime, timedelta

class PowerChangeList(ChangeList):

    def __init__(self, request, model, list_display, list_display_links,
            list_filter, date_hierarchy, search_fields, list_select_related,
            list_per_page, list_max_show_all, list_editable, model_admin):
        #Criando o multi_search_query
        self.multi_search_query = {}
        request.GET._mutable = True
        for k, l, f in model_admin.multi_search:
            if k in request.GET:
                self.multi_search_query[k] = request.GET.get(k, '')
                del request.GET[k]
        request.GET._mutable = False
        super(PowerChangeList, self).__init__(request, model, list_display, list_display_links,
            list_filter, date_hierarchy, search_fields, list_select_related,
            list_per_page, list_max_show_all, list_editable, model_admin)

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None: new_params = {}
        if remove is None: remove = []
        p = self.params.copy()
        for r in remove:
            for k in p.keys():
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        for k, v in self.multi_search_query.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(p)

    def get_query_set(self, request):

        MULTI_SEARCH_VAR = []
        for var, label, query in self.model_admin.multi_search:
            MULTI_SEARCH_VAR.append(var)

        # First, we collect all the declared list filters.
        (self.filter_specs, self.has_filters, remaining_lookup_params,
         use_distinct) = self.get_filters(request)

        # Then, we let every list filter modify the queryset to its liking.
        qs = self.root_query_set
        for filter_spec in self.filter_specs:
            new_qs = filter_spec.queryset(request, qs)
            if new_qs is not None:
                qs = new_qs

        if self.date_hierarchy:
            for key, val in remaining_lookup_params.items():
                if '%s__' % self.date_hierarchy in key:
                    if '/' in val:
                        remaining_lookup_params[key] = datetime.strptime(val, '%d/%m/%Y')
                        if '__lte' in key:
                            remaining_lookup_params[key] = datetime.strptime(val, '%d/%m/%Y') + timedelta(hours=23, minutes=59, seconds=59)
        try:
            # Finally, we apply the remaining lookup parameters from the query
            # string (i.e. those that haven't already been processed by the
            # filters).
            qs = qs.filter(**remaining_lookup_params)
        except (SuspiciousOperation, ImproperlyConfigured):
            # Allow certain types of errors to be re-raised as-is so that the
            # caller can treat them in a special way.
            raise
        except Exception, e:
            # Every other error is caught with a naked except, because we don't
            # have any other way of validating lookup parameters. They might be
            # invalid if the keyword arguments are incorrect, or if the values
            # are not in the correct type, so we might get FieldError,
            # ValueError, ValidationError, or ?.
            raise IncorrectLookupParameters(e)

        # Use select_related() if one of the list_display options is a field
        # with a relationship and the provided queryset doesn't already have
        # select_related defined.
        if not qs.query.select_related:
            if self.list_select_related:
                qs = qs.select_related()
            else:
                for field_name in self.list_display:
                    try:
                        field = self.lookup_opts.get_field(field_name)
                    except models.FieldDoesNotExist:
                        pass
                    else:
                        if isinstance(field.rel, models.ManyToOneRel):
                            qs = qs.select_related()
                            break

        # Set ordering.
        ordering = self.get_ordering(request, qs)
        qs = qs.order_by(*ordering)

        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        #Faz o filter do multi_search
        if self.multi_search_query:
            for k_query, query in self.multi_search_query.items():
                for k, l, f in self.model_admin.multi_search:
                    if k_query == k:
                        fields = f
                        break
                if fields and query:
                    orm_lookups = [construct_search(str(field))
                                   for field in fields]
                    for bit in query.split():
                        or_queries = [models.Q(**{orm_lookup: bit}) for orm_lookup in orm_lookups]
                        qs = qs.filter(reduce(operator.or_, or_queries))

        elif self.search_fields and self.query:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in self.search_fields]
            for bit in self.query.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                qs = qs.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(self.lookup_opts, search_spec):
                        use_distinct = True
                        break

        return qs.distinct()