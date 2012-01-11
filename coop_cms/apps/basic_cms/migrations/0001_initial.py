# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Article'
        db.create_table('basic_cms_article', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(db_index=True, unique=True, max_length=100, blank=True)),
            ('title', self.gf('html_field.db.models.fields.HTMLField')(default=u'Page title')),
            ('content', self.gf('html_field.db.models.fields.HTMLField')(default=u'Page content')),
            ('publication', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('template', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(default='', max_length=100, null=True, blank=True)),
            ('temp_logo', self.gf('django.db.models.fields.files.ImageField')(default='', max_length=100, null=True, blank=True)),
            ('summary', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('section', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='basic_cms_article_rel', null=True, blank=True, to=orm['coop_cms.ArticleSection'])),
        ))
        db.send_create_signal('basic_cms', ['Article'])


    def backwards(self, orm):
        
        # Deleting model 'Article'
        db.delete_table('basic_cms_article')


    models = {
        'basic_cms.article': {
            'Meta': {'object_name': 'Article'},
            'content': ('html_field.db.models.fields.HTMLField', [], {'default': "u'Page content'"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'publication': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'basic_cms_article_rel'", 'null': 'True', 'blank': 'True', 'to': "orm['coop_cms.ArticleSection']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'unique': 'True', 'max_length': '100', 'blank': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'temp_logo': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'title': ('html_field.db.models.fields.HTMLField', [], {'default': "u'Page title'"})
        },
        'coop_cms.articlesection': {
            'Meta': {'object_name': 'ArticleSection'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['basic_cms']
