from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from keyboards.main_menu import get_main_menu
from database import Database

db = Database()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    user = update.effective_user
    user_id = user.id

    # Foydalanuvchini bazaga qo'shish
    db.add_user(
        telegram_id=user_id,
        full_name=f"{user.first_name} {user.last_name or ''}".strip(),
        phone=user.phone_number
    )

    welcome_text = f"""
Assalomu alaykum {user.first_name}! 👋

🤖 **Do'kon BOT** ga xush kelibsiz!

Bu bot orqali siz:
📍 Do'kongacha bo'lgan masofani hisoblashingiz mumkin
📦 Mahsulotlarni boshqarishingiz mumkin
👥 Foydalanuvchi harakatlarini kuzatishingiz mumkin
📊 Ombor hisobini ko'rishingiz mumkin

Quyidagi tugmalardan foydalaning:
    """

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam komandasi"""
    help_text = """
📚 **Botdan foydalanish bo'yicha ko'rsatma:**

📍 **Joylashuv yuborish** - Lokatsiyangizni yuboring va do'kongacha bo'lgan masofani bilib oling

🏪 **Do'konlar** - Barcha do'konlarimiz manzil va koordinatalari

📦 **Mahsulotlar**:
   • Mahsulotlar ro'yxatini ko'rish
   • Yangi mahsulot qo'shish
   • Mahsulot miqdorini o'zgartirish
   • Mahsulotni o'chirish

📊 **Ombor hisobi** - Barcha mahsulotlar miqdori va qiymati

👤 **Profil** - Shaxsiy ma'lumotlar

🛡️ **Admin panel** (faqat admin uchun):
   • Barcha foydalanuvchilar
   • Kirish/chiqish tarixi
   • To'liq statistika
   • Ma'lumotlarni eksport qilish

📞 **Aloqa**: @username
    """

    await update.message.reply_text(
        help_text,
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asosiy menyuga qaytish"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🏠 **Asosiy menyu**\n\nQuyidagi tugmalardan birini tanlang:",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )