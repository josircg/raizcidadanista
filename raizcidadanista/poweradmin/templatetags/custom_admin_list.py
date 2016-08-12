# coding: utf-8
from django.template import Library

register = Library()


def custom_admin_list_filter(cl, spec):
    return {
        'title': spec.title if not callable(spec.title) else spec.title(),
        'choices': list(spec.choices(cl))
    }
custom_admin_list_filter = register.inclusion_tag('admin/custom_filter.html')(custom_admin_list_filter)
