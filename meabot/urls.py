# meabot/urls.py
from django.urls import path
from .views import telegram_webhook, trigger_check_answers

urlpatterns = [
    path('webhook/<path:bot_token>/', telegram_webhook, name='telegram_webhook'),
    path('trigger_check_answers/', trigger_check_answers, name='trigger_check_answers'),
]

# https://api.telegram.org/bot7759043389:AAGUd63ZXpjalTc25N2bwYzvUcPzYabmx5I/setWebhook?url=https://965e-178-91-253-73.ngrok-free.app/meabot/webhook/7759043389:AAGUd63ZXpjalTc25N2bwYzvUcPzYabmx5I/