# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from datetime import datetime
from coop_cms.settings import get_newsletter_item_classes
from coop_cms.models import create_newsletter_item

class Command(BaseCommand):
    help = u"force the creation of every newsletter items"

    def handle(self, *args, **options):
        #look for emailing to be sent
        verbose = options.get('verbosity', 1)
        
        for klass in get_newsletter_item_classes():
            for instance in klass.objects.all():
                item, status = create_newsletter_item(instance)
                if item and status and verbose:
                    print 'create item for', klass.__name__, '-', instance.id, ':', instance
                else:
                    if status and verbose:
                        print 'delete item for', klass.__name__, '-', instance.id, ':', instance
        if verbose:
            print "done"        