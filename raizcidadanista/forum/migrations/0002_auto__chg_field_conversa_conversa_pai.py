# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Conversa.conversa_pai'
        db.alter_column('forum_conversa', 'conversa_pai_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Conversa'], null=True))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Conversa.conversa_pai'
        raise RuntimeError("Cannot reverse this migration. 'Conversa.conversa_pai' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Conversa.conversa_pai'
        db.alter_column('forum_conversa', 'conversa_pai_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Conversa']))

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
            'imagem': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'municipio': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'oficial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'site_externo': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'tipo': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'titulo': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'uf': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']", 'null': 'True', 'blank': 'True'})
        },
        'cadastro.membro': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Membro', '_ormbases': ['cadastro.Pessoa']},
            'aprovador': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'membro_aprovador'", 'null': 'True', 'to': "orm['auth.User']"}),
            'atividade_profissional': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'cpf': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'dtnascimento': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_access_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'filiacao_partidaria': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'filiado': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'municipio_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'nome_da_mae': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'pessoa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cadastro.Pessoa']", 'unique': 'True', 'primary_key': 'True'}),
            'rg': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'secao_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'titulo_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'uf_eleitoral': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']", 'null': 'True', 'blank': 'True'}),
            'usuario': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'membro'", 'null': 'True', 'to': "orm['auth.User']"}),
            'zona_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'})
        },
        'cadastro.pessoa': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Pessoa'},
            'celular': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'dtcadastro': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'municipio': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'residencial': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'sexo': ('django.db.models.fields.CharField', [], {'default': "'O'", 'max_length': '1'}),
            'status_email': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'uf': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'forum.conversa': {
            'Meta': {'object_name': 'Conversa'},
            'arquivo': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'autor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Membro']"}),
            'conversa_pai': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Conversa']", 'null': 'True', 'blank': 'True'}),
            'dt_criacao': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'texto': ('django.db.models.fields.TextField', [], {}),
            'topico': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Topico']"})
        },
        'forum.conversacurtida': {
            'Meta': {'object_name': 'ConversaCurtida'},
            'colaborador': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Membro']"}),
            'conversa': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Conversa']"}),
            'curtida': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'forum.proposta': {
            'Meta': {'object_name': 'Proposta', '_ormbases': ['forum.Conversa']},
            'conversa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['forum.Conversa']", 'unique': 'True', 'primary_key': 'True'}),
            'dt_encerramento': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'forum.topico': {
            'Meta': {'object_name': 'Topico'},
            'criador': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Membro']"}),
            'dt_criacao': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_ultima_atualizacao': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'grupo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Circulo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'titulo': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'visitacoes': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'forum.topicoouvinte': {
            'Meta': {'object_name': 'TopicoOuvinte'},
            'dtentrada': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notificacao': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'ouvinte': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Membro']"}),
            'topico': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Topico']"})
        },
        'forum.voto': {
            'Meta': {'object_name': 'Voto'},
            'eleitor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Membro']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'proposta': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Proposta']"}),
            'voto': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'municipios.uf': {
            'Meta': {'ordering': "(u'nome',)", 'object_name': 'UF'},
            'id_ibge': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'regiao': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'uf': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['forum']