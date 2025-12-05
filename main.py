import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import Config

# Handlerni import qilish
from handlers.start_handler import start_command, help_command, main_menu_callback
from handlers.location_handler import handle_location, store_distance_callback, show_stores_callback
from handlers.product_handler import (
    products_list_callback, add_product_callback, remove_product_callback,
    handle_product_input, handle_removal_input, inventory_stats_callback
)
from handlers.admin_handler import (
    admin_panel_callback, admin_stats_callback, admin_users_callback,
    admin_activities_callback, admin_all_products_callback, export_excel_callback,
    track_special_user_entry, track_special_user_exit
)

# Log sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Asosiy bot funksiyasi"""
    # Botni yaratish
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # Command handlerlar
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("entry", track_special_user_entry))
    application.add_handler(CommandHandler("exit", track_special_user_exit))

    # Location handler
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))

    # Callback query handlerlar
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern='^main_menu$'))
    application.add_handler(
        CallbackQueryHandler(store_distance_callback, pattern='^(store_main|store_branch|nearest_store)$'))
    application.add_handler(CallbackQueryHandler(show_stores_callback, pattern='^show_stores$'))

    # Product handlerlar
    application.add_handler(CallbackQueryHandler(products_list_callback, pattern='^products_list$'))
    application.add_handler(CallbackQueryHandler(add_product_callback, pattern='^add_product$'))
    application.add_handler(CallbackQueryHandler(remove_product_callback, pattern='^remove_product$'))
    application.add_handler(CallbackQueryHandler(inventory_stats_callback, pattern='^inventory_stats$'))

    # Admin handlerlar
    application.add_handler(CallbackQueryHandler(admin_panel_callback, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_stats_callback, pattern='^(admin_stats|export_excel)$'))
    application.add_handler(CallbackQueryHandler(admin_users_callback, pattern='^admin_users$'))
    application.add_handler(CallbackQueryHandler(admin_activities_callback,
                                                 pattern='^(admin_activities|today_activities|weekly_activities)$'))
    application.add_handler(
        CallbackQueryHandler(admin_all_products_callback, pattern='^(admin_all_products|export_products_excel)$'))

    # Text message handlerlar
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_input))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_removal_input))

    # Xatolik handler
    application.add_error_handler(error_handler)

    # Botni ishga tushirish
    logger.info("Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def error_handler(update: object, context):
    """Xatolikni qayta ishlash"""
    logger.error(msg="Xatolik yuz berdi:", exc_info=context.error)

    try:
        await context.bot.send_message(
            chat_id=Config.ADMIN_ID,
            text=f"❌ Botda xatolik yuz berdi:\n\n{context.error}"
        )
    except:
        pass


if __name__ == '__main__':
    main()