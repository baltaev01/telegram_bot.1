from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from keyboards.main_menu import get_admin_keyboard, get_main_menu
from database import Database
from config import Config
from datetime import datetime, timedelta
import pandas as pd
import io

db = Database()


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id == Config.ADMIN_ID


async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panelni ochish"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if not is_admin(user_id):
        await query.edit_message_text(
            "❌ Sizga ruxsat yo'q!",
            reply_markup=get_main_menu()
        )
        return

    admin_text = f"""
🛡️ **ADMIN PANEL**

👤 **Admin**: {query.from_user.full_name}
🆔 **ID**: {user_id}
📅 **Sana**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Quyidagi funksiyalardan foydalanishingiz mumkin:
    """

    await query.edit_message_text(
        admin_text,
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )


async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Umumiy statistika"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Ruxsat yo'q!")
        return

    # Statistikani olish
    stats = db.get_inventory_stats()
    products = db.get_all_products()
    users = db.cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    activities = db.cursor.execute('SELECT COUNT(*) FROM user_activities').fetchone()[0]

    today = datetime.now().strftime('%Y-%m-%d')
    today_activities = db.cursor.execute(
        'SELECT COUNT(*) FROM user_activities WHERE DATE(timestamp) = ?',
        (today,)
    ).fetchone()[0]

    stats_text = f"""
📊 **UMUMIY STATISTIKA**

👥 **Foydalanuvchilar**: {users} ta
📦 **Mahsulot turlari**: {stats[0] or 0} ta
🔢 **Jami mahsulotlar**: {stats[1] or 0} dona
💰 **Jami qiymat**: {stats[2] or 0:,.0f} so'm
📈 **Harakatlar**: {activities} ta
📅 **Bugungi kirishlar**: {today_activities} ta

📋 **Mahsulotlar bo'yicha**:
    """

    if products:
        categories = {}
        for product in products:
            cat = product.get('category', 'Noma\'lum')
            categories[cat] = categories.get(cat, 0) + 1

        stats_text += "\n📂 **Kategoriyalar**:\n"
        for cat, count in categories.items():
            stats_text += f"   • {cat}: {count} ta mahsulot\n"
    else:
        stats_text += "\n⚠️ Mahsulotlar mavjud emas"

    # Oxirgi 5 ta harakat
    recent_activities = db.get_user_activities(date=today)[:5]

    if recent_activities:
        stats_text += f"\n🔄 **Oxirgi 5 ta harakat ({today})**:\n"
        for activity in recent_activities:
            time = activity['timestamp'].split()[1][:5] if 'timestamp' in activity else 'N/A'
            name = activity.get('full_name', 'Noma\'lum')
            action = "Kirish" if activity['action'] == 'entry' else "Chiqish"
            stats_text += f"   • {time} - {name} - {action}\n"

    keyboard = [
        [
            InlineKeyboardButton("📤 Excel eksport", callback_data='export_excel'),
            InlineKeyboardButton("📄 PDF hisobot", callback_data='export_pdf')
        ],
        [InlineKeyboardButton("🔙 Admin panel", callback_data='admin_panel')]
    ]

    await query.edit_message_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchilar ro'yxati"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Ruxsat yo'q!")
        return

    users = db.cursor.execute('''
        SELECT telegram_id, full_name, phone, role, created_at 
        FROM users 
        ORDER BY created_at DESC
    ''').fetchall()

    if not users:
        await query.edit_message_text(
            "👥 Foydalanuvchilar topilmadi",
            reply_markup=get_admin_keyboard()
        )
        return

    users_text = f"""
👥 **FOYDALANUVCHILAR RO'YXATI**

Jami: {len(users)} ta foydalanuvchi

📋 **Ro'yxat**:
    """

    for i, user in enumerate(users[:20], 1):  # Faqat 20 tasini ko'rsatish
        user_id, full_name, phone, role, created_at = user
        users_text += f"\n{i}. **ID**: {user_id}\n"
        users_text += f"   👤 **Ism**: {full_name or 'Noma','lum'}\n"
        users_text += f"   📞 **Tel**: {phone or 'Noma','lum'}\n"
        users_text += f"   🛡️ **Rol**: {role}\n"
        users_text += f"   📅 **Qo'shilgan**: {created_at[:10]}\n"

    if len(users) > 20:
        users_text += f"\n... va yana {len(users) - 20} ta foydalanuvchi"

    keyboard = [
        [
            InlineKeyboardButton("📤 Eksport", callback_data='export_users'),
            InlineKeyboardButton("🔄 Yangilash", callback_data='admin_users')
        ],
        [InlineKeyboardButton("🔙 Admin panel", callback_data='admin_panel')]
    ]

    await query.edit_message_text(
        users_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_activities_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kirish/chiqishlar tarixi"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Ruxsat yo'q!")
        return

    # Oxirgi 50 ta harakatni olish
    activities = db.get_user_activities()[:50]

    if not activities:
        await query.edit_message_text(
            "📊 Harakatlar tarixi topilmadi",
            reply_markup=get_admin_keyboard()
        )
        return

    activities_text = f"""
📊 **KIRISH/CHIQISHLAR TARIXI**

Oxirgi 50 ta harakat:

📋 **Ro'yxat**:
    """

    for i, activity in enumerate(activities, 1):
        user_id = activity['user_id']
        phone = activity.get('phone', 'N/A')
        store = activity['store_name']
        action = "Kirish" if activity['action'] == 'entry' else "Chiqish"
        timestamp = activity['timestamp']
        name = activity.get('full_name', 'Noma\'lum')

        activities_text += f"\n{i}. **{name}**\n"
        activities_text += f"   📞 {phone} | 🏪 {store}\n"
        activities_text += f"   📍 {action} | 🕐 {timestamp}\n"

    # Bugungi statistika
    today = datetime.now().strftime('%Y-%m-%d')
    today_stats = db.cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN action = 'entry' THEN 1 ELSE 0 END) as entries,
            SUM(CASE WHEN action = 'exit' THEN 1 ELSE 0 END) as exits
        FROM user_activities 
        WHERE DATE(timestamp) = ?
    ''', (today,)).fetchone()

    activities_text += f"\n📅 **Bugungi statistika ({today})**:\n"
    activities_text += f"   • Jami harakatlar: {today_stats[0] or 0}\n"
    activities_text += f"   • Kirishlar: {today_stats[1] or 0}\n"
    activities_text += f"   • Chiqishlar: {today_stats[2] or 0}\n"

    keyboard = [
        [
            InlineKeyboardButton("📅 Bugungi", callback_data='today_activities'),
            InlineKeyboardButton("📊 Haftalik", callback_data='weekly_activities')
        ],
        [
            InlineKeyboardButton("📤 Eksport", callback_data='export_activities'),
            InlineKeyboardButton("🔙 Admin panel", callback_data='admin_panel')
        ]
    ]

    await query.edit_message_text(
        activities_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_all_products_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha mahsulotlar"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Ruxsat yo'q!")
        return

    products = db.get_all_products()

    if not products:
        await query.edit_message_text(
            "📦 Mahsulotlar topilmadi",
            reply_markup=get_admin_keyboard()
        )
        return

    products_text = f"""
📦 **BARCHA MAHSULOTLAR**

Jami: {len(products)} ta mahsulot turi

📋 **To'liq ro'yxat**:
    """

    total_quantity = 0
    total_value = 0

    for i, product in enumerate(products, 1):
        quantity = product['quantity']
        price = product.get('price', 0)
        value = quantity * price

        total_quantity += quantity
        total_value += value

        products_text += f"\n{i}. **{product['name']}**\n"
        products_text += f"   🔢 Miqdor: {quantity} dona\n"
        products_text += f"   💰 Narx: {price:,.0f} so'm\n"
        products_text += f"   💵 Qiymat: {value:,.0f} so'm\n"

        if product.get('category'):
            products_text += f"   📂 Kategoriya: {product['category']}\n"

        products_text += f"   🆔 ID: {product['id']}\n"
        products_text += f"   📅 Yangilangan: {product['updated_at'][:10]}\n"

    products_text += f"\n💰 **UMUMIY HISOB**:\n"
    products_text += f"   • Jami dona: {total_quantity} dona\n"
    products_text += f"   • Jami qiymat: {total_value:,.0f} so'm\n"

    keyboard = [
        [
            InlineKeyboardButton("📤 Excel eksport", callback_data='export_products_excel'),
            InlineKeyboardButton("📄 PDF hisobot", callback_data='export_products_pdf')
        ],
        [
            InlineKeyboardButton("✏️ Tahrirlash", callback_data='edit_products'),
            InlineKeyboardButton("🗑️ O'chirish", callback_data='delete_products')
        ],
        [InlineKeyboardButton("🔙 Admin panel", callback_data='admin_panel')]
    ]

    await query.edit_message_text(
        products_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def export_excel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Excel fayl yaratish"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    try:
        # Mahsulotlar ma'lumotlarini olish
        products = db.get_all_products()

        # DataFrame yaratish
        df = pd.DataFrame(products)

        # Excel fayl yaratish
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Mahsulotlar', index=False)

            # Statistika sheet
            stats_data = {
                'Ko\'rsatkich': ['Jami mahsulot turlari', 'Jami dona soni', 'Jami qiymati'],
                'Qiymat': [
                    len(products),
                    df['quantity'].sum() if 'quantity' in df.columns else 0,
                    (df['quantity'] * df['price']).sum() if all(
                        col in df.columns for col in ['quantity', 'price']) else 0
                ]
            }
            pd.DataFrame(stats_data).to_excel(writer, sheet_name='Statistika', index=False)

        output.seek(0)

        # Foydalanuvchiga yuborish
        await context.bot.send_document(
            chat_id=query.from_user.id,
            document=output,
            filename=f'ombor_hisoboti_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            caption='📊 Ombor hisobotining Excel fayli'
        )

        await query.edit_message_text(
            "✅ Excel fayl yuborildi!",
            reply_markup=get_admin_keyboard()
        )

    except Exception as e:
        await query.edit_message_text(
            f"❌ Xatolik yuz berdi: {str(e)}",
            reply_markup=get_admin_keyboard()
        )


async def track_special_user_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maxsus foydalanuvchi kirishini yozish"""
    user_id = update.effective_user.id

    if str(user_id) == str(Config.ADMIN_ID):
        # Maxsus foydalanuvchini kuzatish
        db.log_user_activity(
            user_id=user_id,
            phone='5748140684',
            store_name='Asosiy do\'kon',
            action='entry'
        )

        # Hammaga bildirish
        users = db.cursor.execute('SELECT telegram_id FROM users').fetchall()

        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user[0],
                    text=f"🔄 **Maxsus foydalanuvchi do'konga kirdi**\n\n"
                         f"📞 Telefon: 5748140684\n"
                         f"🕐 Vaqt: {datetime.now().strftime('%H:%M:%S')}\n"
                         f"📅 Sana: {datetime.now().strftime('%Y-%m-%d')}"
                )
            except:
                pass

        await update.message.reply_text(
            "✅ Maxsus foydalanuvchi kirishi yozib olindi va hammaga bildirildi!"
        )


async def track_special_user_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maxsus foydalanuvchi chiqishini yozish"""
    user_id = update.effective_user.id

    if str(user_id) == str(Config.ADMIN_ID):
        # Maxsus foydalanuvchini kuzatish
        db.log_user_activity(
            user_id=user_id,
            phone='5748140684',
            store_name='Asosiy do\'kon',
            action='exit'
        )

        # Hammaga bildirish
        users = db.cursor.execute('SELECT telegram_id FROM users').fetchall()

        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user[0],
                    text=f"🔄 **Maxsus foydalanuvchi do'kondan chiqdi**\n\n"
                         f"📞 Telefon: 5748140684\n"
                         f"🕐 Vaqt: {datetime.now().strftime('%H:%M:%S')}\n"
                         f"📅 Sana: {datetime.now().strftime('%Y-%m-%d')}"
                )
            except:
                pass

        await update.message.reply_text(
            "✅ Maxsus foydalanuvchi chiqishi yozib olindi va hammaga bildirildi!"
        )