# coding: utf-8
from django.contrib.admin.util import reverse_field_path, get_limit_choices_to_from_path

try:
    from django.contrib.admin.filterspecs import FilterSpec, AllValuesFilterSpec
    filterspec = True
except ImportError:
    from django.contrib.admin.filters import AllValuesFieldListFilter, FieldListFilter
    filterspec = False

if filterspec:
    class CustomQuerysetAllValuesFilterSpec(AllValuesFilterSpec):
        def __init__(self, f, request, params, model, model_admin,
                     field_path=None):
            super(CustomQuerysetAllValuesFilterSpec, self).__init__(
                f, request, params, model,
                model_admin,
                field_path=field_path)

            parent_model, reverse_path = reverse_field_path(model, self.field_path)

            queryset = parent_model._default_manager.all()
            qs_dict = getattr(model_admin, 'queryset_filter', None)

            if qs_dict and field_path in qs_dict:
                queryset = qs_dict[field_path]

            if isinstance(queryset, str):
                #Define title
                if hasattr(getattr(model_admin, queryset), 'short_description'):
                    self.title = getattr(getattr(model_admin, queryset), 'short_description')
                queryset = getattr(model_admin, queryset)(request)

            limit_choices_to = get_limit_choices_to_from_path(model, field_path)
            queryset = queryset.filter(limit_choices_to)

            self.lookup_choices = \
                queryset.distinct().order_by(f.name).values_list(f.name, flat=True)

    new_filter_specs = []
    for test, fs in FilterSpec.filter_specs:
        if issubclass(fs, AllValuesFilterSpec):
            new_filter_specs += [(test, CustomQuerysetAllValuesFilterSpec)]
            continue

        new_filter_specs += [(test, fs)]

    FilterSpec.filter_specs = new_filter_specs
else:
    class CustomQuerysetAllValuesFieldListFilter(AllValuesFieldListFilter):
        def __init__(self, field, request, params, model, model_admin, field_path):
            super(CustomQuerysetAllValuesFieldListFilter, self).__init__(
                field, request, params, model, model_admin, field_path)

            parent_model, reverse_path = reverse_field_path(model, self.field_path)

            queryset = parent_model._default_manager.all()
            qs_dict = getattr(model_admin, 'queryset_filter', None)

            if qs_dict and field_path in qs_dict:
                queryset = qs_dict[field_path]

            if isinstance(queryset, str):
                #Define title
                if hasattr(getattr(model_admin, queryset), 'short_description'):
                    self.title = getattr(getattr(model_admin, queryset), 'short_description')
                queryset = getattr(model_admin, queryset)(request)

            limit_choices_to = get_limit_choices_to_from_path(model, field_path)
            queryset = queryset.filter(limit_choices_to)

            self.lookup_choices = queryset.distinct().order_by(field.name).values_list(field.name, flat=True)

    new_filter_list = []
    for test, _filter in FieldListFilter._field_list_filters:
        if issubclass(_filter, AllValuesFieldListFilter):
            new_filter_list += [(test, CustomQuerysetAllValuesFieldListFilter)]
            continue

        new_filter_list += [(test, _filter)]

    FieldListFilter._field_list_filters = new_filter_list
