# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Article.in_newsletter'
        db.add_column('basic_cms_article', 'in_newsletter', self.gf('django.db.models.fields.BooleanField')(default=True), keep_default=False)

        # Adding field 'Article.is_homepage'
        db.add_column('basic_cms_article', 'is_homepage', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Changing field 'Article.content'
        db.alter_column('basic_cms_article', 'content', self.gf('django.db.models.fields.TextField')())


    def backwards(self, orm):
        
        # Deleting field 'Article.in_newsletter'
        db.delete_column('basic_cms_article', 'in_newsletter')

        # Deleting field 'Article.is_homepage'
        db.delete_column('basic_cms_article', 'is_homepage')

        # Changing field 'Article.content'
        db.alter_column('basic_cms_article', 'content', self.gf('html_field.db.models.fields.HTMLField')())


    models = {
        'basic_cms.article': {
            'Meta': {'object_name': 'Article'},
            'content': ('django.db.models.fields.TextField', [], {'default': "u'Page content'"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_newsletter': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_homepage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'publication': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['basic_cms']