# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ApprovalTerms'
        db.create_table('im_approvalterms', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 3, 20, 14, 24, 30, 616341), db_index=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('im', ['ApprovalTerms'])

        # Adding field 'AstakosUser.has_signed_terms'
        db.add_column('im_astakosuser', 'has_signed_terms', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'AstakosUser.date_signed_terms'
        db.add_column('im_astakosuser', 'date_signed_terms', self.gf('django.db.models.fields.DateTimeField')(null=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'ApprovalTerms'
        db.delete_table('im_approvalterms')

        # Deleting field 'AstakosUser.has_signed_terms'
        db.delete_column('im_astakosuser', 'has_signed_terms')

        # Deleting field 'AstakosUser.date_signed_terms'
        db.delete_column('im_astakosuser', 'date_signed_terms')


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
        'im.approvalterms': {
            'Meta': {'object_name': 'ApprovalTerms'},
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 20, 14, 24, 30, 616341)', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'im.astakosuser': {
            'Meta': {'object_name': 'AstakosUser', '_ormbases': ['auth.User']},
            'affiliation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'auth_token': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'auth_token_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'auth_token_expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_signed_terms': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_credits': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_signed_terms': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'invitations': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'is_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'third_party_identifier': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'im.invitation': {
            'Meta': {'object_name': 'Invitation'},
            'accepted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'consumed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inviter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_sent'", 'null': 'True', 'to': "orm['im.AstakosUser']"}),
            'is_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_consumed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'realname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['im']