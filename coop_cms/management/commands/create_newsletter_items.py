# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from datetime import datetime
from coop_cms.settings import get_newsletter_item_classes
from coop_cms.models import NewsletterItem
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = u"force the creation of every newsletter items"

    def handle(self, *args, **options):
        #look for emailing to be sent
        verbose = options.get('verbosity', 1)
        
        for klass in get_newsletter_item_classes():
            for instance in klass.objects.all():
                ct = ContentType.objects.get_for_model(instance)
                item, is_new = NewsletterItem.objects.get_or_create(content_type=ct, object_id=instance.id)
                if is_new and verbose>0:
                    print 'create item for', klass.__name__, '-', instance.id, ':', instance
        if verbose:
            print "done"        