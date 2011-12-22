# -*- coding:utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    url(r'^djaloha/aloah-config.js', 'djaloha.views.aloha_init', name='aloha_init'),
)

urlpatterns += patterns('coop_cms.views',
    url(r'^cms/tree/$', 'process_nav_edition', name='navigation_tree'),
    url(r'^cms/media-images/$', 'show_media_images', name='coop_cms_media_images'),
    url(r'^cms/media-documents/$', 'show_media_documents', name='coop_cms_media_documents'),
    url(r'^upload-image/$', 'upload_image', name="coop_cms_upload_image"),
    
    #keep these at the end
    url(r'^(?P<url>.*)/cms_publish/$', 'publish_article', name='coop_cms_publish_article'),
    url(r'^(?P<url>.*)/cms_edit/$', 'edit_article', name='coop_cms_edit_article'),
    url(r'^(?P<url>.*)/$', 'view_article', name='coop_cms_view_article'),
)
