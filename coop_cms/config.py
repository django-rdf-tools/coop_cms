# -*- coding:utf-8 -*-

from livesettings import config_register, ConfigurationGroup, PositiveIntegerValue, MultipleStringValue
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

not_to_be_mapped = ('south','livesettings','django_extensions','d2rq') 

from django.conf import settings

all_apps=[]
for m in settings.INSTALLED_APPS:
    if(not m.startswith('django.') and m not in not_to_be_mapped):
        all_apps.append((m,m))


COOPTREE_MAPPING = ConfigurationGroup('coop_cms', _('Navigation'))

# Another example of allowing the user to select from several values
config_register(MultipleStringValue(
    COOPTREE_MAPPING,
    'CONTENT_APPS',
    description=_("Applications selection"),
    help_text=_("Selection applications with navigable objects"),
    choices=all_apps,
    default=""
))

