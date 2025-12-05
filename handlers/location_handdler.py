from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler
from keyboards.main_menu import get_store_selection_keyboard, get_main_menu
from utils.distance import calculate_distance, find_nearest_store
from config import Config
from database import Database
from datetime import datetime

db = Database()


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi joylashuvini qabul qilish"""
    user_id = update.effective_user.id
    location = update.message.location

    # Joylashuvni kontekstga saqlash
    context.user_data['user_location'] = (location.latitude, location.longitude)

    await update.message.reply_text(
        "📍 Joylashuvingiz qabul qilindi!\n\n"
        "Qaysi do'konga masofani hisoblamoqchisiz?",
        reply_markup=get_store_selection_keyboard()
    )


async def store_distance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Do'kongacha masofani hisoblash"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if 'user_location' not in context.user_data:
        await query.edit_message_text(
            "❌ Iltimos, avval joylashuvingizni yuboring!\n\n"
            "📍 tugmasini bosing yoki lokatsiya yuboring.",
            reply_markup=get_main_menu()
        )
        return

    user_location = context.user_data['user_location']
    data = query.data

    if data == 'store_main':
        store = Config.STORES['main']
        store_name = "Asosiy do'kon"
    elif data == 'store_branch':
        store = Config.STORES['branch']
        store_name = "Filial do'kon"
    elif data == 'nearest_store':
        nearest_store_name, all_distances = find_nearest_store(user_location, Config.STORES)
        store = Config.STORES[nearest_store_name]
        store_name = store['name']
    else:
        return

    # Masofani hisoblash
    distance_info = calculate_distance(user_location, store['location'])

    result_text = f"""
📍 **{store_name}**

🗺️ **Manzil**: {store.get('address', 'Noma','lum')}

📏 **Masofa**:
   • {distance_info['km']} km
   • {distance_info['meters']} metr

⏱️ **Taxminiy vaqt**:
   • Avtomobil bilan: {distance_info['car_time_minutes']} daqiqa
   • Piyoda: {distance_info['walk_time_minutes']} daqiqa

🌐 **Koordinatalar**:
   • Kenglik: {store['location'][0]}
   • Uzunlik: {store['location'][1]}
    """

    keyboard = [
        [InlineKeyboardButton("📍 Boshqa do'kon", callback_data='show_stores')],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='main_menu')]
    ]

    await query.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_stores_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Do'konlar ro'yxatini ko'rsatish"""
    query = update.callback_query
    await query.answer()

    stores_text = "🏪 **Do'konlarimiz**:\n\n"

    for i, (store_key, store_data) in enumerate(Config.STORES.items(), 1):
        stores_text += f"{i}. **{store_data['name']}**\n"
        stores_text += f"   📍 {store_data.get('address', 'Noma','lum')}\n"
        stores_text += f"   🌐 {store_data['location'][0]}, {store_data['location'][1]}\n\n"

    stores_text += "Joylashuvingizni yuboring va masofani hisoblang!"

    keyboard = [
        [InlineKeyboardButton("📍 Joylashuv yuborish", callback_data='send_location')],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='main_menu')]
    ]

    await query.edit_message_text(
        stores_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )