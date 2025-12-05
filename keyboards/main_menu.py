from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("📍 Joylashuv yuborish", callback_data='send_location'),
            InlineKeyboardButton("🏪 Do'konlar", callback_data='show_stores')
        ],
        [
            InlineKeyboardButton("📦 Mahsulotlar ro'yxati", callback_data='products_list'),
            InlineKeyboardButton("📊 Ombor hisobi", callback_data='inventory_stats')
        ],
        [
            InlineKeyboardButton("➕ Mahsulot qo'shish", callback_data='add_product'),
            InlineKeyboardButton("➖ Mahsulot ayirish", callback_data='remove_product')
        ],
        [
            InlineKeyboardButton("👤 Profil", callback_data='profile'),
            InlineKeyboardButton("ℹ️ Yordam", callback_data='help')
        ]
    ]

    if 5748140684:  # Admin ID
        keyboard.append([
            InlineKeyboardButton("🛡️ Admin panel", callback_data='admin_panel')
        ])

    return InlineKeyboardMarkup(keyboard)


def get_store_selection_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🏪 Asosiy do'kon", callback_data='store_main'),
            InlineKeyboardButton("🏪 Filial", callback_data='store_branch')
        ],
        [
            InlineKeyboardButton("📍 Hammadan yaqin", callback_data='nearest_store'),
            InlineKeyboardButton("🔙 Orqaga", callback_data='main_menu')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📊 Umumiy statistika", callback_data='admin_stats'),
            InlineKeyboardButton("👥 Foydalanuvchilar", callback_data='admin_users')
        ],
        [
            InlineKeyboardButton("📈 Kirish/Chiqishlar", callback_data='admin_activities'),
            InlineKeyboardButton("📦 Barcha mahsulotlar", callback_data='admin_all_products')
        ],
        [
            InlineKeyboardButton("🔧 Sozlamalar", callback_data='admin_settings'),
            InlineKeyboardButton("📤 Eksport", callback_data='admin_export')
        ],
        [
            InlineKeyboardButton("🔙 Asosiy menyu", callback_data='main_menu')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_product_management_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("➕ Yangi mahsulot", callback_data='new_product'),
            InlineKeyboardButton("✏️ Tahrirlash", callback_data='edit_product')
        ],
        [
            InlineKeyboardButton("🗑️ O'chirish", callback_data='delete_product'),
            InlineKeyboardButton("📋 Ro'yxat", callback_data='products_list')
        ],
        [
            InlineKeyboardButton("🔙 Orqaga", callback_data='main_menu')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)