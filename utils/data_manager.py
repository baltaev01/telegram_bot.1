import json
import os
from datetime import datetime
from typing import Dict, List, Any


class DataManager:
    @staticmethod
    def load_data(file_path: str) -> Dict:
        """JSON fayldan ma'lumot yuklash"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Xatolik yuklashda: {e}")
            return {}

    @staticmethod
    def save_data(file_path: str, data: Dict):
        """JSON faylga ma'lumot saqlash"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Xatolik saqlashda: {e}")
            return False

    @staticmethod
    def add_product_to_inventory(product_name: str, quantity: int):
        """Inventorga mahsulot qo'shish"""
        inventory = DataManager.load_data('data/inventory.json')

        if product_name in inventory:
            inventory[product_name] += quantity
        else:
            inventory[product_name] = quantity

        DataManager.save_data('data/inventory.json', inventory)

    @staticmethod
    def remove_product_from_inventory(product_name: str, quantity: int):
        """Inventordan mahsulot ayirish"""
        inventory = DataManager.load_data('data/inventory.json')

        if product_name in inventory:
            if inventory[product_name] >= quantity:
                inventory[product_name] -= quantity
                if inventory[product_name] == 0:
                    del inventory[product_name]
                DataManager.save_data('data/inventory.json', inventory)
                return True
        return False

    @staticmethod
    def track_user_entry(user_id: str, store: str):
        """Foydalanuvchi kirishini yozib qo'yish"""
        today = datetime.now().strftime("%Y-%m-%d")
        tracking = DataManager.load_data('data/tracking.json')

        if today not in tracking:
            tracking[today] = {}

        if store not in tracking[today]:
            tracking[today][store] = []

        entry_time = datetime.now().strftime("%H:%M:%S")
        tracking[today][store].append({
            'user_id': user_id,
            'entry_time': entry_time,
            'exit_time': None
        })

        DataManager.save_data('data/tracking.json', tracking)

    @staticmethod
    def track_user_exit(user_id: str, store: str):
        """Foydalanuvchi chiqishini yozib qo'yish"""
        today = datetime.now().strftime("%Y-%m-%d")
        tracking = DataManager.load_data('data/tracking.json')

        if today in tracking and store in tracking[today]:
            for record in tracking[today][store]:
                if record['user_id'] == user_id and record['exit_time'] is None:
                    record['exit_time'] = datetime.now().strftime("%H:%M:%S")
                    DataManager.save_data('data/tracking.json', tracking)
                    return True
        return False