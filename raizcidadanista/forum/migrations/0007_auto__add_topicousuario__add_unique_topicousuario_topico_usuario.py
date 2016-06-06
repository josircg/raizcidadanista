# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TopicoUsuario'
        db.create_table('forum_topicousuario', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('topico', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Topico'])),
            ('usuario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('num_conversa_lida', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('forum', ['TopicoUsuario'])

        # Adding unique constraint on 'TopicoUsuario', fields ['topico', 'usuario']
        db.create_unique('forum_topicousuario', ['topico_id', 'usuario_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'TopicoUsuario', fields ['topico', 'usuario']
        db.delete_unique('forum_topicousuario', ['topico_id', 'usuario_id'])

        # Deleting model 'TopicoUsuario'
        db.delete_table('forum_topicousuario')


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
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'forum.conversa': {
            'Meta': {'ordering': "('dt_criacao',)", 'object_name': 'Conversa'},
            'arquivo': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'autor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'conversa_pai': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Conversa']", 'null': 'True', 'blank': 'True'}),
            'dt_criacao': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'texto': ('django.db.models.fields.TextField', [], {}),
            'topico': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Topico']"})
        },
        'forum.conversacurtida': {
            'Meta': {'object_name': 'ConversaCurtida'},
            'colaborador': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'conversa': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Conversa']"}),
            'curtida': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'forum.grupo': {
            'Meta': {'object_name': 'Grupo'},
            'descricao': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'forum.grupousuario': {
            'Meta': {'unique_together': "(('grupo', 'usuario'),)", 'object_name': 'GrupoUsuario'},
            'grupo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Grupo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'usuario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'forum.proposta': {
            'Meta': {'ordering': "('dt_criacao',)", 'object_name': 'Proposta', '_ormbases': ['forum.Conversa']},
            'conversa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['forum.Conversa']", 'unique': 'True', 'primary_key': 'True'}),
            'dt_encerramento': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'forum.topico': {
            'Meta': {'ordering': "('-dt_ultima_atualizacao',)", 'object_name': 'Topico'},
            'criador': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'dt_criacao': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_ultima_atualizacao': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'grupo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Grupo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'titulo': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'visitacoes': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'forum.topicoouvinte': {
            'Meta': {'object_name': 'TopicoOuvinte'},
            'dtentrada': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notificacao': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'ouvinte': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'topico': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Topico']"})
        },
        'forum.topicousuario': {
            'Meta': {'unique_together': "(('topico', 'usuario'),)", 'object_name': 'TopicoUsuario'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_conversa_lida': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'topico': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Topico']"}),
            'usuario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'forum.voto': {
            'Meta': {'object_name': 'Voto'},
            'eleitor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'proposta': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Proposta']"}),
            'voto': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['forum']