import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class Database:
    def __init__(self, db_path: str = 'store_bot.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Mahsulotlar jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity INTEGER DEFAULT 0,
                price REAL DEFAULT 0,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Foydalanuvchi harakatlari jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                phone TEXT,
                store_name TEXT NOT NULL,
                action TEXT NOT NULL,  # 'entry' or 'exit'
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Foydalanuvchilar jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                phone TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Do'konlar jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                address TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # Ombordagi harakatlar jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                change_type TEXT NOT NULL,  # 'add', 'remove', 'update'
                quantity_change INTEGER NOT NULL,
                new_quantity INTEGER NOT NULL,
                reason TEXT,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        self.conn.commit()

    # MAHSULOTLAR UCHUN FUNKSIYALAR
    def add_product(self, name: str, quantity: int, price: float = 0, category: str = None) -> bool:
        try:
            self.cursor.execute('''
                INSERT INTO products (name, quantity, price, category) 
                VALUES (?, ?, ?, ?)
            ''', (name, quantity, price, category))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Agar mahsulot mavjud bo'lsa, quantityni yangilaymiz
            self.cursor.execute('''
                UPDATE products 
                SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP 
                WHERE name = ?
            ''', (quantity, name))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding product: {e}")
            return False

    def remove_product(self, name: str, quantity: int) -> bool:
        try:
            self.cursor.execute('SELECT quantity FROM products WHERE name = ?', (name,))
            result = self.cursor.fetchone()

            if not result:
                return False

            current_quantity = result[0]

            if current_quantity < quantity:
                return False

            new_quantity = current_quantity - quantity
            self.cursor.execute('''
                UPDATE products 
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE name = ?
            ''', (new_quantity, name))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error removing product: {e}")
            return False

    def get_all_products(self) -> List[Dict]:
        self.cursor.execute('SELECT * FROM products ORDER BY name')
        columns = [description[0] for description in self.cursor.description]
        products = self.cursor.fetchall()

        return [dict(zip(columns, product)) for product in products]

    def get_product_by_name(self, name: str) -> Optional[Dict]:
        self.cursor.execute('SELECT * FROM products WHERE name = ?', (name,))
        columns = [description[0] for description in self.cursor.description]
        product = self.cursor.fetchone()

        if product:
            return dict(zip(columns, product))
        return None

    def update_product_quantity(self, name: str, quantity: int) -> bool:
        try:
            self.cursor.execute('''
                UPDATE products 
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE name = ?
            ''', (quantity, name))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating product: {e}")
            return False

    # FOYDALANUVCHI HARAKATLARI UCHUN
    def log_user_activity(self, user_id: int, phone: str, store_name: str, action: str) -> bool:
        try:
            self.cursor.execute('''
                INSERT INTO user_activities (user_id, phone, store_name, action) 
                VALUES (?, ?, ?, ?)
            ''', (user_id, phone, store_name, action))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error logging activity: {e}")
            return False

    def get_user_activities(self, user_id: int = None, date: str = None) -> List[Dict]:
        query = '''
            SELECT ua.*, u.full_name 
            FROM user_activities ua
            LEFT JOIN users u ON ua.user_id = u.telegram_id
            WHERE 1=1
        '''
        params = []

        if user_id:
            query += ' AND ua.user_id = ?'
            params.append(user_id)

        if date:
            query += ' AND DATE(ua.timestamp) = ?'
            params.append(date)

        query += ' ORDER BY ua.timestamp DESC'

        self.cursor.execute(query, params)
        columns = [description[0] for description in self.cursor.description]
        activities = self.cursor.fetchall()

        return [dict(zip(columns, activity)) for activity in activities]

    # FOYDALANUVCHILAR UCHUN
    def add_user(self, telegram_id: int, phone: str = None, full_name: str = None, role: str = 'user') -> bool:
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (telegram_id, phone, full_name, role) 
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, phone, full_name, role))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        self.cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        columns = [description[0] for description in self.cursor.description]
        user = self.cursor.fetchone()

        if user:
            return dict(zip(columns, user))
        return None

    # DO'KONLAR UCHUN
    def add_store(self, name: str, latitude: float, longitude: float, address: str = None) -> bool:
        try:
            self.cursor.execute('''
                INSERT INTO stores (name, latitude, longitude, address) 
                VALUES (?, ?, ?, ?)
            ''', (name, latitude, longitude, address))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding store: {e}")
            return False

    def get_all_stores(self) -> List[Dict]:
        self.cursor.execute('SELECT * FROM stores WHERE is_active = 1')
        columns = [description[0] for description in self.cursor.description]
        stores = self.cursor.fetchall()

        return [dict(zip(columns, store)) for store in stores]

    def get_store_by_name(self, name: str) -> Optional[Dict]:
        self.cursor.execute('SELECT * FROM stores WHERE name = ? AND is_active = 1', (name,))
        columns = [description[0] for description in self.cursor.description]
        store = self.cursor.fetchone()

        if store:
            return dict(zip(columns, store))
        return None

    # INVENTORY LOGS
    def log_inventory_change(self, product_id: int, change_type: str, quantity_change: int,
                             new_quantity: int, reason: str = None, user_id: int = None) -> bool:
        try:
            self.cursor.execute('''
                INSERT INTO inventory_logs 
                (product_id, change_type, quantity_change, new_quantity, reason, user_id) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (product_id, change_type, quantity_change, new_quantity, reason, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error logging inventory change: {e}")
            return False

    # STATISTIKA
    def get_inventory_stats(self):
        self.cursor.execute('''
            SELECT 
                COUNT(*) as total_products,
                SUM(quantity) as total_items,
                SUM(quantity * price) as total_value
            FROM products
        ''')
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()