# -*- coding: utf-8 -*-
from django.db import models
from south.modelsinspector import add_introspection_rules

from forms import BRDecimalFormField



class BRDecimalField(models.DecimalField):
    def formfield(self, **kwargs):
        kwargs.update({'form_class': BRDecimalFormField})
        return super(BRDecimalField, self).formfield(**kwargs)

add_introspection_rules([], ["^utils\.fields\.BRDecimalField", ])