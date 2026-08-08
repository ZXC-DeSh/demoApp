import logging
import traceback
import psycopg
from psycopg.rows import dict_row
from DATABASE.config import *
from StaticStorage import Storage


class DatabaseConnection:
    ITEMS_BASE_QUERY = """
        SELECT 
            item_id as id, item_article as article, item_name as name,
            item_edinica as edinica, item_cost as cost, item_deliveryman as deliveryman,
            item_creator as creator, item_category as category, item_sale as sale,
            item_count as count, item_information as information,
            COALESCE(NULLIF(item_picture, ''), 'picture.png') as picture
        FROM Items
    """

    def __init__(self):
        logging.info("Инициализация подключения к базе данных")
        self.connection = self.connect_to_database()
        if self.connection:
            self._rollback_safe()

    def _rollback_safe(self):
        try:
            self.connection.rollback()
        except Exception as e:
            logging.error(f"Ошибка восстановления транзакции: {e}")

    def connect_to_database(self):
        try:
            conn = psycopg.connect(user=user_name, password=user_password, host=host_address, dbname=database_name)
            logging.info(f"Подключено к БД: {conn}")
            return conn
        except Exception as e:
            logging.error(f"Ошибка подключения к БД: {e}")
            return None

    def ensure_connection(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            logging.info("Соединение с БД активно")
        except Exception as e:
            logging.warning(f"Восстановление соединения с БД: {e}")
            if self.connection:
                self.connection.rollback()

    def _fetch(self, query: str, params: tuple = (), fetch_one: bool = False, as_dict: bool = False):
        """Универсальный метод чтения данных из БД"""
        try:
            row_factory = dict_row if as_dict else None
            with self.connection.cursor(row_factory=row_factory) as cursor:
                cursor.execute(query, params)
                return cursor.fetchone() if fetch_one else cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка выполнения запроса чтения: {e}")
            self.connection.rollback()
            return None if fetch_one else []

    def _execute(self, query: str, params: tuple = ()) -> bool:
        """Универсальный метод записи/обновления/удаления"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"Ошибка выполнения записи: {e}")
            self.connection.rollback()
            return False

    # === АВТОРИЗАЦИЯ И ПОЛЬЗОВАТЕЛИ ===

    def check_user_login_password(self, user_login: str, user_password: str) -> bool:
        logging.info(f"Проверка авторизации пользователя: {user_login}")
        query = "SELECT user_login, user_role FROM Client WHERE user_login = %s AND user_password = %s"
        user = self._fetch(query, (user_login, user_password), fetch_one=True, as_dict=True)
        
        if not user:
            logging.warning(f"Пользователь {user_login} не найден или пароль неверен")
            return False

        Storage.set_user_login(user["user_login"])
        Storage.set_user_role(user["user_role"])
        logging.info(f"Пользователь {user_login} успешно авторизован, роль: {user['user_role']}")
        return True

    def take_user_data(self) -> dict:
        user_login = Storage.get_user_login()
        logging.info(f"Получение данных пользователя: {user_login}")
        query = "SELECT user_role, user_name, user_login, user_password FROM Client WHERE user_login = %s"
        res = self._fetch(query, (user_login,), fetch_one=True, as_dict=True)
        
        if not res:
            logging.info("Вход выполнен как гость")
            return {"user_role": "Гость", "user_name": "Аккаунт Гостя"}
        return res

    # === ТОВАРЫ И КАТАЛОГ ===

    def get_all_items(self):
        logging.info("Запрос на получение всех товаров из БД")
        res = self._fetch(self.ITEMS_BASE_QUERY, as_dict=True)
        logging.info(f"Получено товаров из БД: {len(res)}")
        return res

    def search_and_filter_items(self, search_text="", company_filter="", sort_by_count=False, sort_ascending=True):
        logging.info(f"Поиск товаров: текст='{search_text}', фильтр='{company_filter}', сортировка по кол-ву={sort_by_count}")
        query = self.ITEMS_BASE_QUERY + " WHERE 1=1"
        params = []

        if search_text:
            words = [w.strip() for w in search_text.split() if w.strip()]
            fields = ["item_article", "item_name", "item_edinica", "item_deliveryman", "item_creator", "item_category", "item_information"]
            conds = []
            for word in words:
                conds.append(f"({' OR '.join(f'{f} ILIKE %s' for f in fields)})")
                params.extend([f"%{word}%"] * len(fields))
            if conds:
                query += f" AND ({' AND '.join(conds)})"

        if company_filter and company_filter != "Все поставщики":
            query += " AND item_deliveryman = %s"
            params.append(company_filter)

        query += f" ORDER BY item_count {'ASC' if sort_ascending else 'DESC'}" if sort_by_count else " ORDER BY item_name"
        res = self._fetch(query, tuple(params), as_dict=True)
        logging.info(f"Поиск завершен, найдено товаров: {len(res)}")
        return res

    def take_all_deliveryman(self):
        logging.info("Запрос всех поставщиков из БД")
        rows = self._fetch("SELECT DISTINCT item_deliveryman FROM Items ORDER BY item_deliveryman")
        res = ["Все поставщики"] + [r[0] for r in rows if r[0]]
        logging.info(f"Получено поставщиков: {len(res)-1}")
        return res

    def take_item_single_info(self):
        item_id = Storage.get_item_id()
        logging.info(f"Запрос данных товара ID: {item_id}")
        query = """
            SELECT item_id as id, item_article as article, item_name as name,
                   item_edinica as edinica, COALESCE(item_cost, 0.0) as cost,
                   item_deliveryman as deliveryman, item_creator as creator,
                   item_category as category, item_sale as sale, item_count as count,
                   item_information as information, COALESCE(item_picture, '') as picture
            FROM Items WHERE item_id = %s
        """
        res = self._fetch(query, (item_id,), fetch_one=True, as_dict=True) or {}
        if "cost" in res:
            res["cost"] = float(res["cost"])
        return res

    def update_card_picture(self, picture_name: str, user_input_data: list):
        item_id = Storage.get_item_id()
        if len(user_input_data) != 10:
            logging.error(f"ОШИБКА: ожидалось 10 параметров, получено {len(user_input_data)}")
            return False

        query = """
            UPDATE Items SET item_picture=%s, item_article=%s, item_name=%s, item_edinica=%s,
            item_cost=%s, item_deliveryman=%s, item_creator=%s, item_category=%s,
            item_sale=%s, item_count=%s, item_information=%s WHERE item_id=%s
        """
        params = [
            picture_name, user_input_data[0], user_input_data[1], user_input_data[2],
            float(user_input_data[3]) if user_input_data[3] else 0.0,
            user_input_data[4], user_input_data[5], user_input_data[6],
            int(user_input_data[7]) if user_input_data[7] else 0,
            int(user_input_data[8]) if user_input_data[8] else 0,
            user_input_data[9], item_id
        ]
        return self._execute(query, tuple(params))

    def create_new_card(self, user_input: list, picture_name: str):
        query = """
            INSERT INTO Items (item_article, item_name, item_edinica, item_cost, item_deliveryman,
                               item_creator, item_category, item_sale, item_count, item_information, item_picture)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._execute(query, tuple(map(str, user_input)) + (picture_name,))

    def delete_item(self, item_article: str):
        item_id = Storage.get_item_id()
        if self.check_product_in_orders(item_article):
            logging.warning(f"Товар {item_article} используется в заказах, удаление отменено")
            return False
        return self._execute("DELETE FROM Items WHERE item_id = %s", (item_id,))

    def take_all_text_data_for_combo_box(self, type_of_data: str):
        col_map = {"category": "item_category", "deliveryman": "item_deliveryman", "creator": "item_creator"}
        col = col_map.get(type_of_data)
        if not col:
            return []
        query = f"SELECT DISTINCT {col} FROM Items WHERE {col} IS NOT NULL AND {col} != '' ORDER BY {col}"
        return [str(r[0]) for r in self._fetch(query)]

    # === ЗАКАЗЫ И ПВЗ ===

    def take_all_orders_rows(self):
        query = """
            SELECT order_id as id, order_status as status, order_pvz_id_fk as pvz,
                   order_create_date as create_date, order_delivery_date as delivery_date,
                   order_client_name as client_name
            FROM orders ORDER BY order_id
        """
        return self._fetch(query, as_dict=True)

    def take_single_order_data(self):
        order_id = Storage.get_order_id()
        return self.get_order_by_id(order_id) if order_id else {}

    def take_pvz_address(self, pvz_id):
        res = self._fetch("SELECT pvz_address FROM pvz WHERE pvz_id = %s", (pvz_id,), fetch_one=True)
        return res[0] if res else "Адрес не найден"

    def take_all_pvz_addresses(self):
        rows = self._fetch("SELECT pvz_id, pvz_address FROM pvz ORDER BY pvz_id")
        return [f"{r[0]} | {r[1]}" for r in rows]

    def take_all_statuses(self):
        rows = self._fetch("SELECT DISTINCT order_status FROM Orders")
        return [str(r[0]) for r in rows] or ["Новый", "Завершен"]

    def get_order_items_with_prices(self, order_id):
        query = """
            SELECT oi.product_article as article, oi.quantity,
                   COALESCE(i.item_name, 'Товар не найден') as name,
                   COALESCE(i.item_cost, 0) as price
            FROM orderitems oi
            LEFT JOIN items i ON oi.product_article = i.item_article
            WHERE oi.order_id = %s
        """
        return self._fetch(query, (order_id,), as_dict=True)

    def get_order_items(self, order_id):
        items = self.get_order_items_with_prices(order_id)
        for item in items:
            item.pop('price', None)
        return items

    def check_product_in_orders(self, product_article):
        res = self._fetch("SELECT COUNT(*) FROM OrderItems WHERE product_article = %s", (product_article,), fetch_one=True)
        return res[0] > 0 if res else False

    def create_new_order(self, order_data):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(order_id), 0) + 1 FROM Orders")
                next_order_id = cursor.fetchone()[0]

                order_query = """
                    INSERT INTO Orders (order_create_date, order_delivery_date, order_pvz_id_fk,
                                        order_client_name, order_code, order_status)
                    VALUES (CURRENT_DATE, %s, %s, %s, %s, %s) RETURNING order_id
                """
                cursor.execute(order_query, (
                    order_data['delivery_date'], order_data['pvz_id'],
                    order_data['client_name'], order_data['code'], order_data['status']
                ))
                order_id = cursor.fetchone()[0]

                for item in order_data['items']:
                    cursor.execute("INSERT INTO OrderItems (order_id, product_article, quantity) VALUES (%s, %s, %s)",
                                   (order_id, item['article'], item['quantity']))
                    cursor.execute("UPDATE Items SET item_count = item_count - %s WHERE item_article = %s",
                                   (item['quantity'], item['article']))
                
                self.connection.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка создания заказа: {e}")
            traceback.print_exc()
            self.connection.rollback()
            return False

    def update_order_data(self, order_data):
        query = "UPDATE orders SET order_pvz_id_fk = %s, order_status = %s, order_delivery_date = %s WHERE order_id = %s"
        return self._execute(query, (order_data['pvz_id'], order_data['status'], order_data['delivery_date'], order_data['id']))

    def delete_order(self, order_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT product_article, quantity FROM OrderItems WHERE order_id = %s", (order_id,))
                for article, quantity in cursor.fetchall():
                    cursor.execute("UPDATE Items SET item_count = item_count + %s WHERE item_article = %s", (quantity, article))
                cursor.execute("DELETE FROM Orders WHERE order_id = %s", (order_id,))
                self.connection.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка удаления заказа: {e}")
            self.connection.rollback()
            return False

    def get_order_by_id(self, order_id):
        query = """
            SELECT order_id as id, order_create_date as create_date, order_delivery_date as delivery_date,
                   order_pvz_id_fk as pvz, order_status as status, order_client_name as client_name,
                   order_code as code
            FROM orders WHERE order_id = %s
        """
        return self._fetch(query, (order_id,), fetch_one=True, as_dict=True)