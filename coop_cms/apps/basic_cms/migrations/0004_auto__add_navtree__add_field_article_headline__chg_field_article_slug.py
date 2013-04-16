# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'NavTree'
        
        #renamed in coop_cms migration
        
        #db.create_table('basic_cms_navtree', (
        #    ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        #    ('last_update', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        #    ('name', self.gf('django.db.models.fields.CharField')(default='default', unique=True, max_length=100, db_index=True)),
        #))
        #db.send_create_signal('basic_cms', ['NavTree'])
        #
        ## Adding M2M table for field types on 'NavTree'
        #db.create_table('basic_cms_navtree_types', (
        #    ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
        #    ('navtree', models.ForeignKey(orm['basic_cms.navtree'], null=False)),
        #    ('navtype', models.ForeignKey(orm['coop_cms.navtype'], null=False))
        #))
        #db.create_unique('basic_cms_navtree_types', ['navtree_id', 'navtype_id'])

        # Adding field 'Article.headline'
        #db.add_column('basic_cms_article', 'headline',
        #              self.gf('django.db.models.fields.BooleanField')(default=False),
        #              keep_default=False)
        #
        ## Changing field 'Article.slug'
        db.alter_column('basic_cms_article', 'slug', self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=100, separator=u'-', unique=True, populate_from='title', overwrite=False))
        pass

    def backwards(self, orm):
        # Deleting model 'NavTree'
        #db.delete_table('basic_cms_navtree')

        # Removing M2M table for field types on 'NavTree'
        #db.delete_table('basic_cms_navtree_types')

        # Deleting field 'Article.headline'
        db.delete_column('basic_cms_article', 'headline')

        # Changing field 'Article.slug'
        db.alter_column('basic_cms_article', 'slug', self.gf('django.db.models.fields.SlugField')(max_length=100, unique=True))

    models = {
        'basic_cms.article': {
            'Meta': {'object_name': 'Article'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'basic_cms_article_rel'", 'null': 'True', 'blank': 'True', 'to': "orm['coop_cms.ArticleCategory']"}),
            'content': ('django.db.models.fields.TextField', [], {'default': "u'Page content'", 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'headline': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_newsletter': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_homepage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'publication': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '100', 'separator': "u'-'", 'blank': 'True', 'unique': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'summary': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'temp_logo': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'default': "u'Page title'", 'blank': 'True'})
        },
        'basic_cms.navtree': {
            'Meta': {'object_name': 'NavTree'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'default'", 'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['coop_cms.NavType']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'coop_cms.articlecategory': {
            'Meta': {'object_name': 'ArticleCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '100', 'separator': "u'-'", 'blank': 'True', 'unique': 'True', 'populate_from': "'name'", 'overwrite': 'False'})
        },
        'coop_cms.navtype': {
            'Meta': {'object_name': 'NavType'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label_rule': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'search_field': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['basic_cms']