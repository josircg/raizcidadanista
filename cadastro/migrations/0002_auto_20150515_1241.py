# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cadastro', '0001_initial'),
    ]

    operations = [
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
                ('dtcadastro', models.DateField(verbose_name='Dt.Cadastro')),
                ('uf', models.ForeignKey(to='cadastro.UF')),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.AlterModelOptions(
            name='circulomembro',
            options={'verbose_name': 'C\xedrculo do Membro', 'verbose_name_plural': 'C\xedrculos do Membro'},
        ),
        migrations.AlterModelOptions(
            name='membro',
            options={'ordering': ['nome'], 'verbose_name': 'Membro', 'verbose_name_plural': 'Membros'},
        ),
        migrations.RemoveField(
            model_name='membro',
            name='email',
        ),
        migrations.RemoveField(
            model_name='membro',
            name='id',
        ),
        migrations.RemoveField(
            model_name='membro',
            name='nome',
        ),
        migrations.RemoveField(
            model_name='membro',
            name='sexo',
        ),
        migrations.AddField(
            model_name='membro',
            name='aprovador',
            field=models.ForeignKey(related_name='membro_aprovador', verbose_name='Aprovador', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='atividade_profissional',
            field=models.CharField(max_length=150, null=True, verbose_name='Atividade Profissional', blank=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='dtnascimento',
            field=models.DateField(default=datetime.datetime(2015, 5, 15, 12, 41, 31, 206829), verbose_name='Dt.Nascimento'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='membro',
            name='facebook_access_token',
            field=models.TextField(null=True, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='facebook_id',
            field=models.CharField(verbose_name='Facebook ID', max_length=120, null=True, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='filiacao_partidaria',
            field=models.CharField(max_length=100, null=True, verbose_name='Filia\xe7\xe3o Partid\xe1ria', blank=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='municipio_eleitoral',
            field=models.CharField(max_length=150, null=True, verbose_name='Munic\xedpio Eleitoral', blank=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='rg',
            field=models.CharField(max_length=50, null=True, verbose_name='RG', blank=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='titulo_eleitoral',
            field=models.CharField(max_length=50, null=True, verbose_name='T\xedtulo Eleitoral', blank=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='uf_eleitoral',
            field=models.ForeignKey(verbose_name='UF do Domic\xedlio Eleitoral', blank=True, to='cadastro.UF', null=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='usuario',
            field=models.ForeignKey(related_name='membro', verbose_name='Usu\xe1rio', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='circulo',
            name='oficial',
            field=models.BooleanField(default=False, verbose_name='Grupo Oficial'),
        ),
        migrations.AlterField(
            model_name='circulo',
            name='site_externo',
            field=models.URLField(null=True, verbose_name='Site/Blog/Fanpage', blank=True),
        ),
        migrations.AddField(
            model_name='membro',
            name='pessoa_ptr',
            field=models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, default=1, serialize=False, to='cadastro.Pessoa'),
            preserve_default=False,
        ),
    ]
