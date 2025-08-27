# meabot/telegram_handlers.py

import logging
import re
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from .google_sheets import fetch_exchange_opportunities, record_user_question, fetch_internships, fetch_student_discounts
from django.core.cache import cache

logger = logging.getLogger(__name__)

# --------------------------
# small helpers
# --------------------------
def normalize_category(cat: str):
    """
    Normalize human-entered category to a canonical key:
    e.g. "Coffee Shops" -> "coffee_shops"
    """
    if not cat:
        return "uncategorized"
    s = cat.strip().lower()
    s = re.sub(r'&', 'and', s)
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = re.sub(r'_+', '_', s)
    s = s.strip('_')
    return s or "uncategorized"

# Emoji hints for some common keys
CATEGORY_EMOJI = {
    "coffeeshops": "☕",
    "cafe_restaurants": "🍴",
    "beauty_selfcare": "💅",
    "flowers_gifts": "🌸",
    "shopping": "🛍️",
    "storage": "📦",
    "uncategorized": "🎉"
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


def _build_categories_map(discounts_list):
    """
    Returns dict: {category_key: {'label': display_label, 'indices': [idx,...]}}
    """
    mapping = {}
    for idx, d in enumerate(discounts_list):
        raw_cat = d.get('category') or "Uncategorized"
        key = normalize_category(raw_cat)
        mapping.setdefault(key, {"label": raw_cat.strip() or key.replace('_', ' ').title(), "indices": []})
        mapping[key]["indices"].append(idx)
    return mapping


def create_discounts_menu(category=None):
    """Build discounts menu with categories or for a specific category"""

    discounts = get_student_discounts()
    if not discounts:
        # No discounts present
        keyboard = [[back_button("go_back_to_list", "« Main Menu")]]
        text = "🎉 *NU Student Discounts*\n\nNo discounts found at the moment. Please check back later."
        return text, keyboard

    categories_map = _build_categories_map(discounts)

    if not category:
        # Show category selection (build dynamically based on sheet)
        keyboard = []
        # Order categories alphabetically by label (but keep uncategorized last)
        keys_sorted = sorted(categories_map.keys(), key=lambda k: (k == "uncategorized", categories_map[k]["label"].lower()))
        for key in keys_sorted:
            label = categories_map[key]["label"]
            emoji = CATEGORY_EMOJI.get(key, "🎉")
            keyboard.append([InlineKeyboardButton(f"{emoji} {label}", callback_data=f"category_{key}")])

        keyboard.append([back_button("go_back_to_list", "« Main Menu")])

        text = (
            "🎉 *NU Student Discounts*\n\n"
            "Select a category to view offers:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        return text, keyboard

    # Show discounts for the requested category
    keyboard = []
    found = False
    for idx, discount in enumerate(discounts):
        if normalize_category(discount.get("category")) == category:
            found = True
            button = InlineKeyboardButton(
                f"🏪 {discount['organization']}",
                callback_data=f"discount_{idx}"
            )
            keyboard.append([button])

    if not found:
        # No discounts in this category
        keyboard.append([back_button("go_back_to_discounts", "« Back to Categories")])
        text = f"❌ No discounts found for *{category.replace('_', ' ').title()}*."
        return text, keyboard

    # Back to categories
    keyboard.append([back_button("go_back_to_discounts", "« Back to Categories")])

    category_emoji = CATEGORY_EMOJI.get(category, "🎉")
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
    for address in discount.get('addresses', []):
        details_text += f"➖ {address}\n"

    if discount.get('details'):
        details_text += f"\n📝 *Details:*\n{discount['details']}\n\n"
        
    instagram = discount.get('instagram')
    if instagram:
        if instagram.startswith('@'):
            user = instagram[1:]
            formatted_ig = f"[@{user}](https://www.instagram.com/{user}/)"
        else:
            formatted_ig = instagram
        details_text += f"\n📱 *Instagram:* {formatted_ig}\n\n"

    details_text += "_Show student ID to claim!_\n"

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
    """
    Returns cached student discounts, fetching from Google Sheets if not cached.
    """
    cached = cache.get('student_discounts')
    if cached:
        return cached
    try:
        discounts = fetch_student_discounts()
    except Exception as e:
        logger.error(f"Failed to fetch student discounts from sheet: {e}")
        discounts = []
    # ensure cache is set even when fetch failed (so we don't hammer sheet)
    cache.set('student_discounts', discounts, 3600)
    return discounts
