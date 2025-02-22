# meabot/telegram_handlers.py

import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from .google_sheets import fetch_exchange_opportunities, record_user_question, fetch_internships
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Initial seed data (only stored in cache)
STUDENT_DISCOUNTS_INIT = [
    {
        'organization': 'Inhype perfume',
        'addresses': [
            '[Mangilik el 20](https://go.2gis.com/hfrtao)'
        ],
        'discount': '10%',
        'details': '',
        'instagram': '[@inhype_perfume](https://www.instagram.com/inhype_perfume/)'
    },
    {
        'organization': 'CAS beauty spa',
        'addresses': [
            '[Ұлы Дала 39, ЖК «Крокус Cити»](https://go.2gis.com/wsapg)'
        ],
        'discount': '10%',
        'details': '',
        'instagram': '[@cas_beauty_spa](https://www.instagram.com/cas_beauty_spa)'
    },
    {
        'organization': 'Raushan flower boutique',
        'addresses': [
            '[Сәкен Сейфуллин көшесі, 15/4 киоск](https://go.2gis.com/d4aw14)',
            '[Шаймерден Қосшығұлұлы көшесі, 7 киоск](https://go.2gis.com/fl4fs)',
            '[Елубай Тайбеков көшесі, 12а](https://go.2gis.com/4og8jc)'
        ],
        'discount': '15%',
        'details': 'Discount is applicable on all days except 8th of March',
        'instagram': '[@raushan.flowers.kz](https://www.instagram.com/raushan.flowers.kz)'
    },
    {
        'organization': 'Kansul.group',
        'addresses': [
            '[Төле би көшесі, 44/1](https://go.2gis.com/j6s2q)'
        ],
        'discount': '15%',
        'details': '',
        'instagram': '[@kansul.group](https://www.instagram.com/kansul.group)'
    },
    {
        'organization': 'Safar Saqtau',
        'addresses': [
            '[Жумекен Нажимеденов көшесі, 39](https://go.2gis.com/0sewz)'
        ],
        'discount': '15%',
        'details': '',
        'instagram': '[@safarsaqtau](https://www.instagram.com/safarsaqtau)'
    },
    {
        'organization': 'Amari Garden',
        'addresses': [
            '[Сыганак 15/1](https://2gis.kz/astana/geo/70030076302249794)'
        ],
        'discount': '15%',
        'details': '',
        'instagram': '[@amari.garden.flowers](https://www.instagram.com/amari.garden.flowers)'
    },
    {
        'organization': 'Veggie House',
        'addresses': [
            '[Проспект Ұлы Дала, 56/1](https://go.2gis.com/6mvo5)'
        ],
        'discount': '10%',
        'details': '',
        'instagram': '[@veggie_house01](https://www.instagram.com/veggie_house01)'
    },
    {
        'organization': 'Arti Laser',
        'addresses': [
            '[Улица Алихан Бөкейхан, 38](https://go.2gis.com/tcs6nx)'
        ],
        'discount': '25%',
        'details': '',
        'instagram': '[@arti_laser](https://www.instagram.com/arti_laser)'
    },
    {
        'organization': 'BRO GLASSES',
        'addresses': [
            '[ТРЦ MEGA Silk Way, Проспект Кабанбай батыр, 62](https://go.2gis.com/v2o3e)'
        ],
        'discount': '15%',
        'details': '',
        'instagram': '[@broglasses.astana](https://www.instagram.com/broglasses.astana)'
    },
    {
        'organization': 'Plum Tea',
        'addresses': [
            '[ТРЦ Mega Silk Way, 2 этаж](https://go.2gis.com/5c8do)'
        ],
        'discount': '20%',
        'details': '',
        'instagram': '[@plum.tea](https://www.instagram.com/plumtea.kz)'
    },
    {
        'organization': 'Jasyl coffee',
        'addresses': [
            '[Улица Достық, 13](https://go.2gis.com/qgihxd)'
        ],
        'discount': '10%',
        'details': 'Except delivery, only for drinks',
        'instagram': '[@jasylcoffee](https://www.instagram.com/jasylcoffee)'
    },
    {
        'organization': 'Teadot',
        'addresses': [
            '[Д.Қона ев 14/2](https://go.2gis.com/ux9yc)',
            '[Тәуелсіздік 34/2](https://go.2gis.com/gjk2t)'
        ],
        'discount': '10%',
        'details': '',
        'instagram': '[@teadot_astana](https://www.instagram.com/teadot_astana)'
    },
    {
        'organization': 'Nanduk',
        'addresses': [
            '[Сарайшык 4](https://2gis.kz/astana/inside/70030076191027893/firm/70000001078305896)',
            '[Туркестан 28/2](https://2gis.kz/astana/branches/70000001078305895/firm/70000001080861419)',
            '[Mega Silk Way](https://2gis.kz/astana/branches/70000001078305895/firm/70000001089538096)',
            '[ТРЦ Аружан](https://2gis.kz/astana/branches/70000001078305895/firm/70000001091494803)'
        ],
        'discount': '5%',
        'details': 'From 10am to 6pm\nExcept Tuesday (50% because of the student day)',
        'instagram': '[@nanduk_astana](https://www.instagram.com/nanduk_astana)'
    },
    {
        'organization': 'Moon Collection',
        'addresses': [
            '[Мангилик Ел 36](https://go.2gis.com/GmPtV)'
        ],
        'discount': '10%',
        'details': 'Until the end of may',
        'instagram': '[@moon.collection.kz](https://www.instagram.com/moon.collection.kz)'
    },
    {
        'organization': 'Focus Telo',
        'addresses': [
            '[Кайым Мухамедханов 4Б блок H​](https://go.2gis.com/K96VT)'
        ],
        'discount': '10%',
        'details': '',
        'instagram': '[@focustelo](https://www.instagram.com/focustelo)'
    },
    {
        'organization': 'Lammi Me',
        'addresses': [
            '[Туран, 55/10, 1 этаж​](https://go.2gis.com/ry77j)'
        ],
        'discount': '10%',
        'details': 'Free brow lamination on the first visit',
        'instagram': '[@lammi.me](https://www.instagram.com/lammi.me)'
    },
    {
        'organization': 'Dodo Pizza',
        'addresses': [
            '[All Branches​]()'
        ],
        'discount': '10% - 15%',
        'details': '10% discount on online orders using the promo code: NU10\n\n15% discount on offline orders at Dodo Pizza using the promo code: NU15',
        'instagram': '[@dodopizza_astana](https://www.instagram.com/dodopizza_astana)'
    },
    {
        'organization': 'Essence',
        'addresses': [
            '[Косшыгулулы, 7​](https://go.2gis.com/XZgud)'
        ],
        'discount': '10% - 15%',
        'details': 'Does not apply on individual orders.\nВход с салона красоты "Сулу"',
        'instagram': '[@essence.ast](https://www.instagram.com/essence.ast?igsh=azJlaHd0YzA1djNk)'
    }
]

CATEGORIZED_DISCOUNTS = {
    "coffeeshops": [9, 10, 11],        # Plum Tea, Jasyl Coffee, Teadot
    "cafe_restaurants": [16, 12, 6],   # DODO Pizza, Nanduk, Veggie House
    "beauty_selfcare": [15, 0, 1, 7], # Lammi.me, Inhype, CAS, Arti Laser
    "flowers_gifts": [2, 5],           # Raushan, Amari Garden
    "shopping": [8, 13, 14, 17],      # BRO Glasses, Moon, Focustelo, Essence
    "storage": [4, 3]                 # Safar Saqtau, Kansul Group
}

def back_button(callback_data: str, text: str="« Back"):
    """Helper function to build a 'Back' button with some emoji style."""
    return InlineKeyboardButton(text, callback_data=callback_data)

# --------------------------
# /start Handler
# --------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        "✨ *Welcome to the MEA bot!* ✨\n\n"
        "Here you can explore:\n"
        "• Exchange opportunities 🌍\n"
        "• Internships 💼\n"
        "• Exclusive student discounts 🎉\n\n"
        "🔹 Type /list to see all opportunities\n"
        "🔹 /discounts for student discounts\n"
        "🔹 /help for more info\n"
        "🔹 /ask to submit questions!\n\n"
        "Have fun exploring! 🚀"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


# --------------------------
# /help Handler
# --------------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "ℹ️ *Bot Guide*\n\n"
        "• /list - Explore opportunities (Exchanges and Internships)\n"
        "• /discounts - Exclusive student discounts 🎉\n"
        "• /ask - Submit your question to us\n"
        "Enjoy our bot! ✨"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def discounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle both command and callback navigation"""
    if update.message:  # Original command
        message = update.message
    else:  # Callback navigation
        message = update.callback_query.message

    text, keyboard = create_discounts_menu()
    await message.reply_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def create_discounts_menu(category=None):
    """Build discounts menu with categories"""
    if not category:
        # Show category selection
        keyboard = [
            [InlineKeyboardButton("☕ Coffeeshops", callback_data="category_coffeeshops")],
            [InlineKeyboardButton("🍴 Cafes & Restaurants", callback_data="category_cafe_restaurants")],
            [InlineKeyboardButton("💅 Beauty & Self-Care", callback_data="category_beauty_selfcare")],
            [InlineKeyboardButton("🌸 Flowers & Gifts", callback_data="category_flowers_gifts")],
            [InlineKeyboardButton("🛍️ Shopping", callback_data="category_shopping")],
            [InlineKeyboardButton("📦 Storage", callback_data="category_storage")],
            [back_button("go_back_to_list", "« Main Menu")]
        ]
        
        text = (
            "🎉 *NU Student Discounts*\n\n"
            "Select a category to view offers:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        return text, keyboard
    
    # Show discounts for specific category
    keyboard = []
    for idx in CATEGORIZED_DISCOUNTS.get(category, []):
        discount = get_student_discounts()[idx]
        button = InlineKeyboardButton(
            f"🏪 {discount['organization']}",
            callback_data=f"discount_{idx}"
        )
        keyboard.append([button])
    
    keyboard.append([back_button("go_back_to_discounts", "« Back to Categories")])
    
    category_emoji = {
        "coffeeshops": "☕",
        "cafe_restaurants": "🍴",
        "beauty_selfcare": "💅",
        "flowers_gifts": "🌸",
        "shopping": "🛍️",
        "storage": "📦"
    }.get(category, "🎉")
    
    text = (
        f"{category_emoji} *{category.replace('_', ' ').title()} Discounts*\n\n"
        "Select an organization:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    return text, keyboard

# --------------------------
# /list Handler
# --------------------------
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Shows categories: Exchanges, Internships, Student Discounts (inline buttons).
    """
    keyboard = [
        [InlineKeyboardButton("🌍 Exchanges", callback_data="list_exchanges")],
        [InlineKeyboardButton("💼 Internships", callback_data="list_internships")],
        [InlineKeyboardButton("🎉 Student Discounts", callback_data="go_back_to_discounts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "📋 *Available Categories:*\n\n"
        "1) Exchanges 🌍\n"
        "2) Internships 💼\n"
        "3) Student Discounts 🎉\n\n"
        "Select one below!"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# --------------------------
# CallbackQuery Handler
# --------------------------
async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    # Add category handlers
    if data.startswith("category_"):
        category = data.split("_", 1)[1]
        text, keyboard = create_discounts_menu(category)
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # Existing exchange handlers
    elif data == "list_exchanges":
        await show_exchanges(query, context)
    elif data == "list_internships":
        await show_internships(query, context)
    elif data.startswith("exchange_"):
        index = int(data.split("_")[1])
        await show_exchange_details(query, context, index)

    # New internship handlers
    elif data.startswith("internship_"):
        index = int(data.split("_")[1])
        await show_internship_details(query, context, index)
    elif data == "go_back_to_internships_list":
        await show_internships(query, context)

    # Existing discount handlers
    elif data.startswith("discount_"):
        index = int(data.split("_")[1])
        await show_discount_details(query, context, index)
    
    # Update back button handler
    elif data == "go_back_to_discounts":
        text, keyboard = create_discounts_menu()
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Existing navigation handlers
    elif data == "go_back_to_list":
        await go_back_to_list(query)
    elif data.startswith("go_back_to_exchange_list"):
        await show_exchanges(query, context)
    else:
        await query.edit_message_text("❓ Unknown action. Please go back or try again.")


async def show_discount_details(query, context, index):
    """
    Shows detailed information about a specific discount
    """
    discounts = get_student_discounts()
    if index < 0 or index >= len(discounts):
        return
    discount = discounts[index]

    details_text = (
        f"🏢 *{discount['organization']}*\n\n"
        f"💰 *Discount:* `{discount['discount']}`\n\n"
        "📌 *Addresses:*\n"
    )

    # Add all addresses
    for address in discount['addresses']:
        details_text += f"➖ {address}\n"

    if discount['details']:
        details_text += f"\n📝 *Details:*\n`{discount['details']}`\n"

    details_text += (
        f"\n📱 *Instagram:* {discount['instagram']}\n\n"
        "_Show student ID to claim!_\n"
    )

    keyboard = [
        [back_button("go_back_to_discounts", "« Back to Discounts")]
    ]

    await query.edit_message_text(
        text=details_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

async def show_exchanges(query, context):
    """
    Displays the list of exchange programs as clickable inline buttons.
    """
    exchanges = fetch_exchange_opportunities()
    if not exchanges:
        await query.edit_message_text(
            text="🚫 No Exchange Opportunities found. Check back soon!"
        )
        return

    keyboard = []
    for idx, item in enumerate(exchanges):
        program_name = item['program_name']
        button = InlineKeyboardButton(
            f"🌍 {program_name}",
            callback_data=f"exchange_{idx}"
        )
        keyboard.append([button])

    # Add a back button to the main list
    keyboard.append([back_button("go_back_to_list", "« Back to Categories")])

    text = (
        "🌍 *Exchange Opportunities:*\n\n"
        "Below are the available programs. Tap one for more details!\n"
    )
    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_exchange_details(query, context, index):
    """
    Show the details of a specific exchange program by index.
    """
    exchanges = fetch_exchange_opportunities()
    if index < 0 or index >= len(exchanges):
        await query.edit_message_text("⚠️ Invalid exchange index.")
        return

    opp = exchanges[index]

    # Format registration period with calendar emoji
    registration_period = f"{opp['start_reg']}  →  {opp['end_reg']}"

    details_text = (
        f"🎓 *{opp['program_name']}*\n\n"
        "🌟 *Program Details:*\n\n"
        f"🏛️ *Partner University:*\n`{opp['partner_university']}`\n\n"
        f"🎯 *Eligibility:*\n`{opp['who_can_apply']}`\n\n"
        f"🗓️ *Registration Period:*\n`{registration_period}`\n\n"
        f"⏳ *Program Duration:*\n`{opp['duration']}`\n\n"
        f"🌐 *Official Website:* [Visit Site]({opp['website']})\n\n"
        "_Need more info? Use_ /ask _to contact us!_ 💬"
    )

    keyboard = [
        [back_button("go_back_to_exchange_list", "« Back to Exchanges List")]
    ]

    await query.edit_message_text(
        text=details_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True  # Disable link preview for cleaner look
    )

async def go_back_to_list(query):
    """
    Re-displays the main list of categories
    """
    keyboard = [
        [InlineKeyboardButton("🌍 Exchanges", callback_data="list_exchanges")],
        [InlineKeyboardButton("💼 Internships", callback_data="list_internships")],
        [InlineKeyboardButton("🎉 Student Discounts", callback_data="go_back_to_discounts")]
    ]
    text = (
        "📋 *Available Categories:*\n\n"
        "1) Exchanges 🌍\n"
        "2) Internships 💼\n"
        "3) Student Discounts 🎉\n\n"
        "Select one below!"
    )
    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_internships(query, context):
    """Displays the list of internship programs"""
    internships = fetch_internships()
    if not internships:
        await query.edit_message_text(
            text="💼 No internship opportunities available at the moment. Check back later!",
            reply_markup=InlineKeyboardMarkup([
                [back_button("go_back_to_list", "« Back to Categories")]
            ])
        )
        return

    keyboard = []
    for idx, internship in enumerate(internships):
        button = InlineKeyboardButton(
            f"💼 {internship['internship_program']}",
            callback_data=f"internship_{idx}"
        )
        keyboard.append([button])
    
    keyboard.append([back_button("go_back_to_list", "« Back to Categories")])

    text = (
        "💼 *Internships*\n\n"
        "Available internships:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_internship_details(query, context, index):
    """Shows detailed information about a specific internship"""
    internships = fetch_internships()
    if index < 0 or index >= len(internships):
        await query.edit_message_text("⚠️ Invalid internship selection.")
        return

    internship = internships[index]

    details_text = (
        f"🏢 *{internship['internship_program']}*\n\n"
        f"📚 *Field/Department:* {internship['field_department']}\n\n"
        f"⏳ *Duration & Details:*\n{internship['duration_details']}\n\n"
        f"📍 *Location:* {internship['location']}\n\n"
        f"📅 *Application Deadline:* {internship['application_deadline']}\n\n"
        f"🔗 *Application Link:* [Apply Here]({internship['application_link']})\n\n"
        "_Need more info? Use_ /ask _to contact us!_ 💬"
    )

    keyboard = [
        [back_button("go_back_to_internships_list", "« Back to Internships")]
    ]

    await query.edit_message_text(
        text=details_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

# --------------------------
# /ask Handler
# --------------------------
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    When the user types /ask, we'll prompt them to type their question next.
    """
    await update.message.reply_text(
        "❓ *Submit Your Question*\n\n"
        "Please type *your question* about exchanges or *your suggestion* about discounts now.\n" 
        "We'll save it and answer you soon! 📝",
        parse_mode="Markdown"
    )
    context.user_data["awaiting_question"] = True

# --------------------------
# Message Handler (next text)
# --------------------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Catches text messages that are not commands
    """
    if context.user_data.get("awaiting_question"):
        question_text = update.message.text
        user_id = update.effective_user.id
        username = update.effective_user.username or "N/A"

        record_user_question(user_id, username, question_text)

        await update.message.reply_text(
            "✅ *Question Recorded!*\n\n"
            "Thanks for your submission. We'll review and respond soon. ✨\n",
            parse_mode="Markdown"
        )
        context.user_data["awaiting_question"] = False
    else:
        await update.message.reply_text(
            "🤔 Not sure what you meant. Try these commands:\n"
            "• /help - Instructions\n"
            "• /list - Categories\n"
            "• /discounts - Student offers\n"
            "• /ask - Ask a question"
        )

def get_student_discounts():
    cached = cache.get('student_discounts')
    if not cached:
        cache.set('student_discounts', STUDENT_DISCOUNTS_INIT, 3600)
    return cached or STUDENT_DISCOUNTS_INIT