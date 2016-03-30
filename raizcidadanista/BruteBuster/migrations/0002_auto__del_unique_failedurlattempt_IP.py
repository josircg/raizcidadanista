# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'FailedURLAttempt', fields ['IP']
        db.delete_unique('BruteBuster_failedurlattempt', ['IP'])


    def backwards(self, orm):
        # Adding unique constraint on 'FailedURLAttempt', fields ['IP']
        db.create_unique('BruteBuster_failedurlattempt', ['IP'])


    models = {
        'BruteBuster.failedattempt': {
            'IP': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'Meta': {'ordering': "['-timestamp']", 'unique_together': "(('username', 'IP'),)", 'object_name': 'FailedAttempt'},
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'BruteBuster.failedurlattempt': {
            'IP': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'Meta': {'ordering': "['-timestamp']", 'object_name': 'FailedURLAttempt'},
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['BruteBuster']