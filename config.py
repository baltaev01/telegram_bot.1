import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 5748140684))

    STORES = {
        'main': {
            'name': 'Asosiy Do\'kon',
            'location': (float(os.getenv('MAIN_STORE_LAT', 41.311081)),
                         float(os.getenv('MAIN_STORE_LON', 69.240562))),
            'address': 'Toshkent sh., Yunusobod tumani'
        },
        'branch': {
            'name': 'Filial Do\'kon',
            'location': (float(os.getenv('BRANCH_STORE_LAT', 41.338133)),
                         float(os.getenv('BRANCH_STORE_LON', 69.332839))),
            'address': 'Toshkent sh., Mirzo Ulug\'bek tumani'
        }
    }