# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType
import config # not unused, needed by livesettings !
from livesettings import config_value
from django.conf import settings
from django.utils.importlib import import_module

def get_navigable_content_types():
    ct_choices = []
    content_apps = config_value(u'coop_cms', 'CONTENT_APPS')
    apps_labels = [app.rsplit('.')[-1] for app in content_apps]
    navigable_content_types = ContentType.objects.filter(app_label__in=apps_labels).order_by('app_label')
    for ct in navigable_content_types:
        is_navnode = ((ct.model == 'navnode') and (ct.app_label == 'coop_cms'))
        if (not is_navnode) and 'get_absolute_url' in dir(ct.model_class()):
            ct_choices.append((ct.id, ct.app_label+u'.'+ct.model))
    return ct_choices

def get_article_class():
    if hasattr(get_article_class, '_cache_class'):
        return getattr(get_article_class, '_cache_class')
    else:
        article_class = None
        try:
            full_class_name = getattr(settings, 'COOP_CMS_ARTICLE_CLASS')
            module_name, class_name = full_class_name.rsplit('.', 1)
            module = import_module(module_name)
            article_class = getattr(module, class_name)
        
        except AttributeError:
            if 'coop_cms.apps.basic_cms' in settings.INSTALLED_APPS:
                from coop_cms.apps.basic_cms.models import Article
                article_class = Article
        
        if not article_class:
            raise Exception('No article class configured')
        
        setattr(get_article_class, '_cache_class', article_class)
        return article_class
    
def get_article_form():
    try:
        full_class_name = getattr(settings, 'COOP_CMS_ARTICLE_FORM')
        module_name, class_name = full_class_name.rsplit('.', 1)
        module = import_module(module_name)
        article_form = getattr(module, class_name)
    
    except AttributeError:
        from coop_cms.forms import ArticleForm
        article_form = ArticleForm
    
    return article_form

def get_article_templates(article, user):
    try:
        full_class_name = getattr(settings, 'COOP_CMS_ARTICLE_TEMPLATES')
        module_name, object_name = full_class_name.rsplit('.', 1)
        module = import_module(module_name)
        article_templates_object = getattr(module, object_name)
        if callable(article_templates_object):
            article_templates = article_templates_object(article, user)
        else:
            article_templates = article_templates_object
    
    except AttributeError:
        article_templates = None
    
    return article_templates

def get_article_logo_size(article):
    try:
        get_size_name = getattr(settings, 'COOP_CMS_ARTICLE_LOGO_SIZE')
        try:
            module_name, fct_name = get_size_name.rsplit('.', 1)
            module = import_module(module_name)
            get_size = getattr(module, fct_name)
            if callable(get_size):
                size = get_size(article)
            else:
                size = get_size
        except ValueError:
            size = get_size_name
    
    except AttributeError:
        size = "48x48"
    return size