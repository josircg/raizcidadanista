# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Circulo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('titulo', models.CharField(max_length=80, verbose_name='T\xedtulo')),
                ('descricao', models.TextField(verbose_name='Descricao')),
                ('tipo', models.CharField(max_length=1, verbose_name='Tipo', choices=[(b'R', 'Regional'), (b'T', 'Tem\xe1tico')])),
                ('municipio', models.CharField(max_length=150, null=True, verbose_name='Munic\xedpio', blank=True)),
                ('oficial', models.BooleanField(verbose_name='Grupo Oficial')),
                ('dtcadastro', models.DateField(verbose_name='Dt.Cadastro')),
                ('site_externo', models.URLField(verbose_name='Site/Blog/Fanpage')),
            ],
            options={
                'verbose_name': 'C\xedrculo',
            },
        ),
        migrations.CreateModel(
            name='CirculoEvento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=100, verbose_name='T\xedtulo')),
                ('dt_evento', models.DateTimeField(verbose_name='Dt.Evento')),
                ('local', models.TextField(verbose_name='Local do Evento')),
                ('circulo', models.ForeignKey(to='cadastro.Circulo')),
            ],
        ),
        migrations.CreateModel(
            name='CirculoMembro',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('administrador', models.BooleanField()),
                ('circulo', models.ForeignKey(to='cadastro.Circulo')),
            ],
        ),
        migrations.CreateModel(
            name='Membro',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=150, verbose_name='Nome Completo')),
                ('email', models.EmailField(max_length=254, verbose_name='Email', blank=True)),
                ('sexo', models.CharField(default=b'O', max_length=1, choices=[(b'M', 'Masculino'), (b'F', 'Feminino'), (b'O', 'Outros')])),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='UF',
            fields=[
                ('codigo', models.CharField(max_length=2, serialize=False, primary_key=True)),
                ('nome', models.CharField(max_length=30)),
                ('regiao', models.CharField(max_length=2, choices=[(b'N', 'Norte'), (b'NE', 'Nordeste'), (b'S', 'Sul'), (b'SE', 'Sudeste'), (b'CO', 'Centro Oeste')])),
            ],
        ),
        migrations.AddField(
            model_name='circulomembro',
            name='membro',
            field=models.ForeignKey(to='cadastro.Membro'),
        ),
        migrations.AddField(
            model_name='circulo',
            name='uf',
            field=models.ForeignKey(blank=True, to='cadastro.UF', null=True),
        ),
    ]
