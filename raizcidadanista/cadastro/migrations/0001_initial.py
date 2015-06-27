# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Pessoa'
        db.create_table('cadastro_pessoa', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nome', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('uf', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['municipios.UF'])),
            ('municipio', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('sexo', self.gf('django.db.models.fields.CharField')(default='O', max_length=1)),
            ('celular', self.gf('django.db.models.fields.CharField')(max_length=14, null=True, blank=True)),
            ('residencial', self.gf('django.db.models.fields.CharField')(max_length=14, null=True, blank=True)),
            ('dtcadastro', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now, blank=True)),
        ))
        db.send_create_signal('cadastro', ['Pessoa'])

        # Adding model 'Membro'
        db.create_table('cadastro_membro', (
            ('pessoa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cadastro.Pessoa'], unique=True, primary_key=True)),
            ('atividade_profissional', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('dtnascimento', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('rg', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('titulo_eleitoral', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('uf_eleitoral', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['municipios.UF'], null=True, blank=True)),
            ('municipio_eleitoral', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('filiacao_partidaria', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('usuario', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='membro', null=True, to=orm['auth.User'])),
            ('facebook_id', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('facebook_access_token', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aprovador', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='membro_aprovador', null=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('cadastro', ['Membro'])

        # Adding model 'Circulo'
        db.create_table('cadastro_circulo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('titulo', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('descricao', self.gf('django.db.models.fields.TextField')()),
            ('tipo', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('uf', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['municipios.UF'], null=True, blank=True)),
            ('municipio', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('oficial', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('dtcadastro', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now)),
            ('site_externo', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('cadastro', ['Circulo'])

        # Adding model 'CirculoMembro'
        db.create_table('cadastro_circulomembro', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('circulo', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cadastro.Circulo'])),
            ('membro', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cadastro.Membro'])),
            ('administrador', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('cadastro', ['CirculoMembro'])

        # Adding model 'CirculoEvento'
        db.create_table('cadastro_circuloevento', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('circulo', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cadastro.Circulo'])),
            ('nome', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('dt_evento', self.gf('django.db.models.fields.DateTimeField')()),
            ('local', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('cadastro', ['CirculoEvento'])


    def backwards(self, orm):
        # Deleting model 'Pessoa'
        db.delete_table('cadastro_pessoa')

        # Deleting model 'Membro'
        db.delete_table('cadastro_membro')

        # Deleting model 'Circulo'
        db.delete_table('cadastro_circulo')

        # Deleting model 'CirculoMembro'
        db.delete_table('cadastro_circulomembro')

        # Deleting model 'CirculoEvento'
        db.delete_table('cadastro_circuloevento')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'cadastro.circulo': {
            'Meta': {'object_name': 'Circulo'},
            'descricao': ('django.db.models.fields.TextField', [], {}),
            'dtcadastro': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'municipio': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'oficial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'site_externo': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'tipo': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'titulo': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'uf': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']", 'null': 'True', 'blank': 'True'})
        },
        'cadastro.circuloevento': {
            'Meta': {'object_name': 'CirculoEvento'},
            'circulo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Circulo']"}),
            'dt_evento': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local': ('django.db.models.fields.TextField', [], {}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'cadastro.circulomembro': {
            'Meta': {'object_name': 'CirculoMembro'},
            'administrador': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'circulo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Circulo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'membro': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Membro']"})
        },
        'cadastro.membro': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Membro', '_ormbases': ['cadastro.Pessoa']},
            'aprovador': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'membro_aprovador'", 'null': 'True', 'to': "orm['auth.User']"}),
            'atividade_profissional': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'dtnascimento': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_access_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'filiacao_partidaria': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'municipio_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'pessoa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cadastro.Pessoa']", 'unique': 'True', 'primary_key': 'True'}),
            'rg': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'titulo_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'uf_eleitoral': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']", 'null': 'True', 'blank': 'True'}),
            'usuario': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'membro'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'cadastro.pessoa': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Pessoa'},
            'celular': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'dtcadastro': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'municipio': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'residencial': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'sexo': ('django.db.models.fields.CharField', [], {'default': "'O'", 'max_length': '1'}),
            'uf': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'municipios.uf': {
            'Meta': {'ordering': "(u'nome',)", 'object_name': 'UF'},
            'id_ibge': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'regiao': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'uf': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['cadastro']