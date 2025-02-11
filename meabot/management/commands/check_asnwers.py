from django.core.management.base import BaseCommand
from meabot.google_sheets import check_and_send_pending_answers
from meabot.bot import application

class Command(BaseCommand):
    help = 'Check the Questions sheet for new answers and send them to users.'

    def handle(self, *args, **options):
        check_and_send_pending_answers(application)
        self.stdout.write(self.style.SUCCESS('Checked and sent pending answers.'))