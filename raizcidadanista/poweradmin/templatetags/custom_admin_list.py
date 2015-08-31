# coding: utf-8
from django.template import Library
from datetime import datetime
import re

register = Library()


def custom_admin_list_filter(cl, spec):
    return {
        'title': spec.title if not callable(spec.title) else spec.title(),
        'choices': list(spec.choices(cl))
    }
custom_admin_list_filter = register.inclusion_tag('admin/custom_filter.html')(custom_admin_list_filter)


@register.simple_tag
def readonly(cl, result, item):
    if result.form and 'name="form' in item:
        readonly_fields = cl.model_admin.get_readonly_fields(cl.request, result.form.instance)

        fieldrex = re.compile(r'(name="form-)(\d+)(-)([\w\-]+)"')
        field_name = fieldrex.findall(item)[0][3]
        if field_name in readonly_fields:
            valuerex = re.compile(r'(value=")([\S ]*)(" id)')
            value = valuerex.findall(item)[0][1]
            item = item.replace('type="text"', 'type="hidden"').replace('</td>', '%s</td>' % value)

    return item

@register.filter(name='strptime')
def strptime(value, mash):
    return datetime.strptime(value, mash)