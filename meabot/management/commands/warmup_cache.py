from django.core.management.base import BaseCommand
from django.core.cache import cache
from meabot.google_sheets import fetch_student_discounts, fetch_exchange_opportunities, fetch_internships

class Command(BaseCommand):
    help = 'Preload essential data into cache'

    def handle(self, *args, **options):
        self.stdout.write("Warming up cache (discounts, exchanges, internships)...")
        try:
            # Each fetch_* function sets cache internally.
            fetch_student_discounts()
            fetch_exchange_opportunities()
            fetch_internships()
            self.stdout.write(self.style.SUCCESS('Cache warmed up successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Cache warmup failed: {e}'))
