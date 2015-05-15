# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
                ('oficial', models.BooleanField(default=False, verbose_name='Grupo Oficial')),
                ('dtcadastro', models.DateField(verbose_name='Dt.Cadastro')),
                ('site_externo', models.URLField(null=True, verbose_name='Site/Blog/Fanpage', blank=True)),
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
            options={
                'verbose_name': 'C\xedrculo do Membro',
                'verbose_name_plural': 'C\xedrculos do Membro',
            },
        ),
        migrations.CreateModel(
            name='Pessoa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=150, verbose_name='Nome Completo')),
                ('municipio', models.CharField(max_length=150, verbose_name='Munic\xedpio')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('sexo', models.CharField(default=b'O', max_length=1, choices=[(b'M', 'Masculino'), (b'F', 'Feminino'), (b'O', 'Outros')])),
                ('celular', models.CharField(help_text='Ex.: (XX)XXXXX-XXXX', max_length=14, null=True, blank=True)),
                ('residencial', models.CharField(help_text='Ex.: (XX)XXXXX-XXXX', max_length=14, null=True, blank=True)),
                ('dtcadastro', models.DateField(default=datetime.datetime.now, verbose_name='Dt.Cadastro')),
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
        migrations.CreateModel(
            name='Membro',
            fields=[
                ('pessoa_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cadastro.Pessoa')),
                ('atividade_profissional', models.CharField(max_length=150, null=True, verbose_name='Atividade Profissional', blank=True)),
                ('dtnascimento', models.DateField(verbose_name='Dt.Nascimento')),
                ('rg', models.CharField(max_length=50, null=True, verbose_name='RG', blank=True)),
                ('titulo_eleitoral', models.CharField(max_length=50, null=True, verbose_name='T\xedtulo Eleitoral', blank=True)),
                ('municipio_eleitoral', models.CharField(max_length=150, null=True, verbose_name='Munic\xedpio Eleitoral', blank=True)),
                ('filiacao_partidaria', models.CharField(max_length=100, null=True, verbose_name='Filia\xe7\xe3o Partid\xe1ria', blank=True)),
                ('facebook_id', models.CharField(verbose_name='Facebook ID', max_length=120, null=True, editable=False, blank=True)),
                ('facebook_access_token', models.TextField(null=True, editable=False, blank=True)),
                ('aprovador', models.ForeignKey(related_name='membro_aprovador', verbose_name='Aprovador', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('uf_eleitoral', models.ForeignKey(verbose_name='UF do Domic\xedlio Eleitoral', blank=True, to='cadastro.UF', null=True)),
                ('usuario', models.ForeignKey(related_name='membro', verbose_name='Usu\xe1rio', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['nome'],
                'verbose_name': 'Membro',
                'verbose_name_plural': 'Membros',
            },
            bases=('cadastro.pessoa',),
        ),
        migrations.AddField(
            model_name='pessoa',
            name='uf',
            field=models.ForeignKey(to='cadastro.UF'),
        ),
        migrations.AddField(
            model_name='circulo',
            name='uf',
            field=models.ForeignKey(blank=True, to='cadastro.UF', null=True),
        ),
        migrations.AddField(
            model_name='circulomembro',
            name='membro',
            field=models.ForeignKey(to='cadastro.Membro'),
        ),
    ]
