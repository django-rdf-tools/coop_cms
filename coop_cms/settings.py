from django.contrib.contenttypes.models import ContentType
import config # not unused, needed by livesettings !
from livesettings import config_value
from django.conf import settings
from django.utils.importlib import import_module

def get_navigable_content_types():
    ct_choices = []
    content_apps = config_value(u'coop_cms', 'CONTENT_APPS')
    navigable_content_types = ContentType.objects.filter(app_label__in=content_apps).order_by('app_label')
    for ct in navigable_content_types:
        is_navnode = ((ct.model == 'navnode') and (ct.app_label == 'coop_cms'))
        if (not is_navnode) and 'get_absolute_url' in dir(ct.model_class()):
            ct_choices.append((ct.id, ct.app_label+u'.'+ct.model))
    return ct_choices
        

def get_article_class():
    try:
        full_class_name = getattr(settings, 'COOP_CMS_ARTICLE_CLASS')
        module_name, class_name = full_class_name.rsplit('.', 1)
        module = import_module(module_name)
        return getattr(module, class_name)
    
    except AttributeError:
        from coop_cms.models import CmsArticle
        return CmsArticle
