# meabot/bot.py

import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, PicklePersistence
from .telegram_handlers import (
    start_command, help_command, list_command, inline_button_handler, ask_command, message_handler, discounts_command
)
import os
import telegram.ext

TELEGRAM_BOT_TOKEN  = os.environ.get('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

application = (
    ApplicationBuilder()
    .token(TELEGRAM_BOT_TOKEN)
    .persistence(telegram.ext.PicklePersistence(filepath='meabot_data.pickle'))
    .build()
)

# Register all your handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("list", list_command))
application.add_handler(CommandHandler("discounts", discounts_command))
application.add_handler(CallbackQueryHandler(inline_button_handler))

application.add_handler(CommandHandler("ask", ask_command))

application.add_handler(CallbackQueryHandler(inline_button_handler))

# Catch-all text messages that are not commands
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
)