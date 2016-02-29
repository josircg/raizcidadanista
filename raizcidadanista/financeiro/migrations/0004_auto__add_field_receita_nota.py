# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Receita.nota'
        db.add_column('financeiro_receita', 'nota',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Receita.nota'
        db.delete_column('financeiro_receita', 'nota')


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
        'cadastro.membro': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Membro', '_ormbases': ['cadastro.Pessoa']},
            'aprovador': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'membro_aprovador'", 'null': 'True', 'to': "orm['auth.User']"}),
            'assinado': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'atividade_profissional': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'contrib_prox_pgto': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'contrib_tipo': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'contrib_valor': ('utils.fields.BRDecimalField', [], {'default': '0', 'max_digits': '7', 'decimal_places': '2'}),
            'cpf': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'dt_prefiliacao': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'dtnascimento': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'endereco': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'endereco_cep': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'endereco_complemento': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'endereco_num': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'estadocivil': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'facebook_access_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'filiacao_partidaria': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'filiado': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fundador': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'municipio_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'municipio_naturalidade': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'nome_da_mae': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'pessoa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cadastro.Pessoa']", 'unique': 'True', 'primary_key': 'True'}),
            'rg': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'secao_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'titulo_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'twitter_id': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'twitter_oauth_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'twitter_oauth_token_secret': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'uf_eleitoral': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']", 'null': 'True', 'blank': 'True'}),
            'uf_naturalidade': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'uf_naturalidade'", 'null': 'True', 'to': "orm['municipios.UF']"}),
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
            'status_email': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'uf': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'financeiro.conta': {
            'Meta': {'ordering': "('conta',)", 'object_name': 'Conta'},
            'ativa': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'conta': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'descricao': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nota': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tipo': ('django.db.models.fields.CharField', [], {'default': "'M'", 'max_length': '1'})
        },
        'financeiro.metaarrecadacao': {
            'Meta': {'object_name': 'MetaArrecadacao'},
            'data_inicial': ('django.db.models.fields.DateField', [], {}),
            'data_limite': ('django.db.models.fields.DateField', [], {}),
            'descricao': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'valor': ('utils.fields.BRDecimalField', [], {'max_digits': '12', 'decimal_places': '2'})
        },
        'financeiro.receita': {
            'Meta': {'ordering': "('conta__conta',)", 'object_name': 'Receita'},
            'colaborador': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Membro']", 'null': 'True', 'blank': 'True'}),
            'conta': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['financeiro.Conta']"}),
            'dtaviso': ('django.db.models.fields.DateField', [], {}),
            'dtpgto': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nota': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'valor': ('utils.fields.BRDecimalField', [], {'max_digits': '12', 'decimal_places': '2'})
        },
        'municipios.uf': {
            'Meta': {'ordering': "(u'nome',)", 'object_name': 'UF'},
            'id_ibge': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'regiao': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'uf': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['financeiro']