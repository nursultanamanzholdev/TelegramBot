from django.core.management.base import BaseCommand
from django.core.cache import cache
from meabot.telegram_handlers import STUDENT_DISCOUNTS_INIT

class Command(BaseCommand):
    help = 'Preload essential data into cache'

    def handle(self, *args, **options):
        cache.set('student_discounts', STUDENT_DISCOUNTS_INIT, 3600)
        self.stdout.write(self.style.SUCCESS('Cache warmed up successfully'))