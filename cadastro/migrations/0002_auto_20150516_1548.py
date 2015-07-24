# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membro',
            name='dtnascimento',
            field=models.DateField(null=True, verbose_name='Dt.Nascimento', blank=True),
        ),
    ]
