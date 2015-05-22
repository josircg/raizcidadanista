# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0003_auto_20150518_0921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='circulo',
            name='uf',
            field=models.ForeignKey(blank=True, to='municipios.UF', null=True),
        ),
        migrations.AlterField(
            model_name='membro',
            name='uf_eleitoral',
            field=models.ForeignKey(verbose_name='UF do Domic\xedlio Eleitoral', blank=True, to='municipios.UF', null=True),
        ),
        migrations.AlterField(
            model_name='pessoa',
            name='uf',
            field=models.ForeignKey(to='municipios.UF'),
        ),
        migrations.DeleteModel(
            name='UF',
        ),
    ]
