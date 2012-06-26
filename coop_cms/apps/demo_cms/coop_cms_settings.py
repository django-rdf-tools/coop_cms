# -*- coding: utf-8 -*-

COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.Article'
COOP_CMS_ARTICLE_FORM = 'coop_cms.apps.demo_cms.forms.ArticleForm'

COOPBAR_MODULES = ('coop_cms.apps.demo_cms.my_coop_bar',)
DJALOHA_LINK_MODELS = ('demo_cms.Article',)
COOP_CMS_ARTICLE_LOGO_SIZE = "128x128"

COOP_CMS_ARTICLE_TEMPLATES = 'coop_cms.apps.demo_cms.get_article_templates'
#COOP_CMS_ARTICLE_TEMPLATES = (
#    ('standard.html', 'Standard'),
#    ('homepage.html', 'Homepage'),
#    ('blog.html', 'Blog'),
#)

COOP_CMS_SITE_PREFIX = 'http://127.0.0.1:8000'
COOP_CMS_FROM_EMAIL = '"Your name" <your@email.com>'
COOP_CMS_TEST_EMAILS = ('"Your name" <your@email.com>',)
COOP_CMS_NEWSLETTER_TEMPLATES = (
    ('basic_newsletter.html', 'Basic'),
    ('special_newsletter.html', 'With categories'),
    ('sortable_newsletter.html', 'Sortable categories'),
)
COOP_CMS_NEWSLETTER_FORM = 'coop_cms.apps.demo_cms.forms.SortableNewsletterForm'