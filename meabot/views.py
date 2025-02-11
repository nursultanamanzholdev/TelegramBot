# meabot/views.py
import json
import os
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from telegram import Update
from asgiref.sync import async_to_sync
from .bot import application

initialized = False

@csrf_exempt
async def telegram_webhook(request, bot_token):
    global initialized
    if request.method == "POST" and bot_token == application.bot.token:
        if not initialized:
            await application.initialize()
            initialized = True

        data = json.loads(request.body.decode('utf-8'))
        update = Update.de_json(data, application.bot)
        await application.process_update(update)

    return HttpResponse("OK", status=200)


@csrf_exempt
@require_GET
def trigger_check_answers(request):
    # Use a secret token stored in environment variables for security
    secret = request.GET.get('secret')
    if secret != os.environ.get('CHECK_ANSWERS_SECRET', 'default-secret'):
        return HttpResponseForbidden("Forbidden")
    
    # Call your function to check pending answers.
    from meabot.google_sheets import check_and_send_pending_answers
    from meabot.bot import application
    check_and_send_pending_answers(application)
    return HttpResponse("Check executed successfully.")


def keep_alive(request):
    return HttpResponse("I am alive!")
