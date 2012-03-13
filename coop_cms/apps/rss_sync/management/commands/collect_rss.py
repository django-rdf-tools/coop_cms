from django.core.management.base import BaseCommand
from coop_cms.apps.rss_sync.utils import collect_all_rss_items

class Command(BaseCommand):
    help = "for all source models, collect rss feed and create items"

    def handle(self, *args, **options):
        collect_all_rss_items()