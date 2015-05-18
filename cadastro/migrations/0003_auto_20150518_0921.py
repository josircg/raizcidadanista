# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0002_auto_20150516_1548'),
    ]

    operations = [
        migrations.AlterField(
            model_name='circulomembro',
            name='administrador',
            field=models.BooleanField(default=False),
        ),
    ]
