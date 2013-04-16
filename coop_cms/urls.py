# -*- coding:utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.views.generic.detail import DetailView
from coop_cms.settings import get_article_class

urlpatterns = patterns('coop_cms.views',
    url(r'^cms/tree/(?P<tree_id>\d*)/$', 'process_nav_edition', name='navigation_tree'),
    url(r'^cms/media-images/$', 'show_media', {'media_type': 'image'}, name='coop_cms_media_images'),
    url(r'^cms/media-documents/$', 'show_media', {'media_type': 'document'}, name='coop_cms_media_documents'),
    url(r'^cms/upload-image/$', 'upload_image', name="coop_cms_upload_image"),
    url(r'^cms/upload-doc/$', 'upload_doc', name="coop_cms_upload_doc"),
    url(r'^cms/change-template/(?P<article_id>\d*)/$', 'change_template', name="coop_cms_change_template"),
    url(r'^cms/settings/(?P<article_id>\d*)/$', 'article_settings', name="coop_cms_article_settings"),
    url(r'^cms/new/$', 'new_article', name="coop_cms_new_article"),
    url(r'^cms/update-logo/(?P<article_id>\d*)/$', 'update_logo', name="coop_cms_update_logo"),
    url(r'^cms/private-download/(?P<doc_id>\d*)/$', 'download_doc', name='coop_cms_download_doc'),
    url(r'^cms/articles/$', 'view_all_articles', name="coop_cms_view_all_articles"),
    url(r'^cms/set-homepage/(?P<article_id>\d*)/$', 'set_homepage', name='coop_cms_set_homepage'),
    url(r'^cms/newsletter/new/$', 'new_newsletter', name='coop_cms_new_newsletter'),
    url(r'^cms/newsletter/settings/(?P<newsletter_id>\d+)/$', 'new_newsletter', name='coop_cms_newsletter_settings'),
    url(r'^cms/newsletter/(?P<newsletter_id>\d+)/$', 'view_newsletter', name='coop_cms_view_newsletter'),
    url(r'^cms/newsletter/(?P<newsletter_id>\d+)/cms_edit/$', 'edit_newsletter', name='coop_cms_edit_newsletter'),
    url(r'^cms/newsletter/change-template/(?P<newsletter_id>\d+)/$', 'change_newsletter_template', name="coop_cms_change_newsletter_template"),
    url(r'^cms/newsletter/test/(?P<newsletter_id>\d+)/$', 'test_newsletter', name="coop_cms_test_newsletter"),
    url(r'^cms/newsletter/schedule/(?P<newsletter_id>\d+)/$', 'schedule_newsletter_sending', name="coop_cms_schedule_newsletter_sending"),
    url(r'sitemap/$', 'tree_map', name="default_site_map"),
    url(r'articles/(?P<slug>[-\w]+)/$', 'articles_category', name="coop_cms_articles_category"),

    # url(r'^articles/(?P<slug>\w+)/$', DetailView.as_view(   model=get_article_class(),
    #                                                         context_object_name="category",
    #                                                         template_name="coop_cms/articles_category.html"
    #                                                         ),
    #                                                         name="articles_category"),
    )

if 'coop_cms.apps.rss_sync' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^rss-sync/', include('coop_cms.apps.rss_sync.urls')),
    )

urlpatterns += patterns('coop_cms.views',
    #keep these at the end
    url(r'^(?P<url>.*)/cms_publish/$', 'publish_article', name='coop_cms_publish_article'),
    url(r'^(?P<url>.*)/cms_edit/$', 'edit_article', name='coop_cms_edit_article'),
    url(r'^(?P<url>.*)/cms_cancel/$', 'cancel_edit_article', name='coop_cms_cancel_edit_article'),
    url(r'^(?P<url>.*)/$', 'view_article', name='coop_cms_view_article'),
    url(r'^$', 'homepage', name='coop_cms_homepage'),
)


