from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from keyboards.main_menu import get_main_menu, get_product_management_keyboard
from database import Database
import re

db = Database()


async def products_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mahsulotlar ro'yxatini ko'rsatish"""
    query = update.callback_query
    await query.answer()

    products = db.get_all_products()

    if not products:
        await query.edit_message_text(
            "📦 Mahsulotlar ro'yxati bo'sh\n\n"
            "Yangi mahsulot qo'shish uchun '➕ Mahsulot qo'shish' tugmasini bosing.",
            reply_markup=get_main_menu()
        )
        return

    products_text = "📦 **Mahsulotlar ro'yxati**:\n\n"
    total_value = 0

    for i, product in enumerate(products, 1):
        price = product.get('price', 0)
        value = price * product['quantity']
        total_value += value

        products_text += f"{i}. **{product['name']}**\n"
        products_text += f"   Miqdor: {product['quantity']} dona\n"
        if price > 0:
            products_text += f"   Narx: {price:,.0f} so'm\n"
            products_text += f"   Qiymat: {value:,.0f} so'm\n"

        if product.get('category'):
            products_text += f"   Kategoriya: {product['category']}\n"

        products_text += "\n"

    products_text += f"\n💰 **Jami qiymat**: {total_value:,.0f} so'm"

    keyboard = [
        [
            InlineKeyboardButton("➕ Qo'shish", callback_data='add_product'),
            InlineKeyboardButton("➖ Ayirish", callback_data='remove_product')
        ],
        [
            InlineKeyboardButton("📊 Statistika", callback_data='inventory_stats'),
            InlineKeyboardButton("🏠 Asosiy", callback_data='main_menu')
        ]
    ]

    await query.edit_message_text(
        products_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def add_product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mahsulot qo'shish boshlanishi"""
    query = update.callback_query
    await query.answer()

    context.user_data['awaiting_product'] = True

    await query.edit_message_text(
        "➕ **Yangi mahsulot qo'shish**\n\n"
        "Mahsulot nomini quyidagi formatda yuboring:\n\n"
        "`Nomi: Miqdori: Narxi: Kategoriyasi`\n\n"
        "*Misollar:*\n"
        "`Kola: 100: 8000: Ichimliklar`\n"
        "`Non: 50: 3000: Non mahsulotlari`\n"
        "`Sut: 20` (faqat nom va miqdor)\n\n"
        "Bekor qilish uchun: /cancel",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Bekor qilish", callback_data='cancel_add')]
        ])
    )


async def handle_product_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mahsulot ma'lumotlarini qabul qilish"""
    if not context.user_data.get('awaiting_product'):
        return

    user_input = update.message.text

    if user_input.lower() == '/cancel':
        context.user_data.pop('awaiting_product', None)
        await update.message.reply_text(
            "❌ Mahsulot qo'shish bekor qilindi.",
            reply_markup=get_main_menu()
        )
        return

    # Ma'lumotlarni ajratib olish
    parts = user_input.split(':')

    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Noto'g'ri format! Iltimos, quyidagi formatda yuboring:\n"
            "`Nomi: Miqdori: Narxi: Kategoriyasi`\n\n"
            "Yoki bekor qilish: /cancel",
            parse_mode='Markdown'
        )
        return

    try:
        name = parts[0].strip()
        quantity = int(parts[1].strip()) if len(parts) > 1 else 0
        price = float(parts[2].strip()) if len(parts) > 2 and parts[2].strip() else 0
        category = parts[3].strip() if len(parts) > 3 else None

        # Mahsulotni bazaga qo'shish
        success = db.add_product(name, quantity, price, category)

        if success:
            # Log yozish
            product = db.get_product_by_name(name)
            if product:
                db.log_inventory_change(
                    product_id=product['id'],
                    change_type='add',
                    quantity_change=quantity,
                    new_quantity=product['quantity'],
                    reason='Foydalanuvchi tomonidan qo\'shildi',
                    user_id=update.effective_user.id
                )

            response = f"""
✅ **Mahsulot muvaffaqiyatli qo'shildi!**

📦 **Nomi**: {name}
🔢 **Miqdori**: {quantity} dona
💰 **Narxi**: {price:,.0f} so'm
📂 **Kategoriya**: {category or 'Noma','lum'}

Jami qiymat: {price * quantity:,.0f} so'm
            """

            # Foydalanuvchini bazada yangilash
            db.add_user(
                telegram_id=update.effective_user.id,
                full_name=f"{update.effective_user.first_name} {update.effective_user.last_name or ''}",
                phone=update.effective_user.phone_number
            )

        else:
            response = "❌ Mahsulot qo'shishda xatolik yuz berdi!"

        context.user_data.pop('awaiting_product', None)

        keyboard = [
            [
                InlineKeyboardButton("📦 Barcha mahsulotlar", callback_data='products_list'),
                InlineKeyboardButton("➕ Yangi qo'shish", callback_data='add_product')
            ],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='main_menu')]
        ]

        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except ValueError as e:
        await update.message.reply_text(
            f"❌ Raqamli qiymatlarni noto'g'ri kiritdingiz!\n"
            f"Xatolik: {str(e)}\n\n"
            "Qayta urinib ko'ring yoki /cancel ni bosing."
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Xatolik yuz berdi: {str(e)}\n\n"
            "Qayta urinib ko'ring yoki /cancel ni bosing."
        )


async def remove_product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mahsulot ayirish"""
    query = update.callback_query
    await query.answer()

    context.user_data['awaiting_removal'] = True

    await query.edit_message_text(
        "➖ **Mahsulot ayirish**\n\n"
        "Qaysi mahsulotdan qancha ayirmoqchisiz?\n\n"
        "Format: `Mahsulot nomi: Miqdori`\n\n"
        "*Misollar:*\n"
        "`Kola: 10`\n"
        "`Non: 5`\n\n"
        "Bekor qilish: /cancel",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Bekor qilish", callback_data='cancel_remove')]
        ])
    )


async def handle_removal_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mahsulot ayirish ma'lumotlarini qabul qilish"""
    if not context.user_data.get('awaiting_removal'):
        return

    user_input = update.message.text

    if user_input.lower() == '/cancel':
        context.user_data.pop('awaiting_removal', None)
        await update.message.reply_text(
            "❌ Mahsulot ayirish bekor qilindi.",
            reply_markup=get_main_menu()
        )
        return

    try:
        parts = user_input.split(':')
        if len(parts) != 2:
            raise ValueError("Format noto'g'ri")

        name = parts[0].strip()
        quantity = int(parts[1].strip())

        # Mahsulotni bazadan ayirish
        success = db.remove_product(name, quantity)

        if success:
            # Log yozish
            product = db.get_product_by_name(name)
            if product:
                db.log_inventory_change(
                    product_id=product['id'],
                    change_type='remove',
                    quantity_change=-quantity,
                    new_quantity=product['quantity'],
                    reason='Foydalanuvchi tomonidan ayirildi',
                    user_id=update.effective_user.id
                )

            response = f"""
✅ **Mahsulot muvaffaqiyatli ayirildi!**

📦 **Nomi**: {name}
🔢 **Ayirildi**: {quantity} dona
📊 **Qoldi**: {product['quantity'] if product else 0} dona
            """
        else:
            response = f"""
❌ **Mahsulot ayirish mumkin emas!**

Sabablar:
1. Mahsulot topilmadi
2. Yetarli miqdor yo'q
3. Xatolik yuz berdi

Iltimos, qayta tekshiring.
            """

        context.user_data.pop('awaiting_removal', None)

        keyboard = [
            [
                InlineKeyboardButton("📦 Barcha mahsulotlar", callback_data='products_list'),
                InlineKeyboardButton("➖ Boshqa ayirish", callback_data='remove_product')
            ],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='main_menu')]
        ]

        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format! Iltimos, quyidagi formatda yuboring:\n"
            "`Mahsulot nomi: Miqdori`\n\n"
            "Yoki bekor qilish: /cancel",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Xatolik yuz berdi: {str(e)}\n\n"
            "Qayta urinib ko'ring yoki /cancel ni bosing."
        )


async def inventory_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ombor statistikasi"""
    query = update.callback_query
    await query.answer()

    stats = db.get_inventory_stats()
    products = db.get_all_products()

    if not stats:
        await query.edit_message_text(
            "📊 Ombor statistikasi mavjud emas",
            reply_markup=get_main_menu()
        )
        return

    total_products, total_items, total_value = stats

    stats_text = f"""
📊 **OMBOR STATISTIKASI**

📦 **Jami mahsulot turlari**: {total_products or 0}
🔢 **Jami dona soni**: {total_items or 0} dona
💰 **Jami qiymati**: {total_value or 0:,.0f} so'm

📈 **Mahsulotlar bo'yicha**:
    """

    if products:
        # Eng ko'p va eng kam miqdordagi mahsulotlar
        sorted_products = sorted(products, key=lambda x: x['quantity'], reverse=True)

        stats_text += "\n🏆 **Eng ko'p miqdor**:\n"
        for product in sorted_products[:3]:
            stats_text += f"   • {product['name']}: {product['quantity']} dona\n"

        stats_text += "\n📉 **Eng kam miqdor**:\n"
        for product in sorted_products[-3:]:
            stats_text += f"   • {product['name']}: {product['quantity']} dona\n"
    else:
        stats_text += "\n⚠️ Mahsulotlar mavjud emas"

    keyboard = [
        [
            InlineKeyboardButton("📦 Barcha mahsulotlar", callback_data='products_list'),
            InlineKeyboardButton("📤 Eksport", callback_data='export_stats')
        ],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='main_menu')]
    ]

    await query.edit_message_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )