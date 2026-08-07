import logging
import traceback
import psycopg
from DATABASE.config import *
from StaticStorage import Storage


class DatabaseConnection:
    def __init__(self):
        """ Конструктор класса """
        logging.info("Инициализация подключения к базе данных")
        self.connection = self.connect_to_database()
        if self.connection:
            try:
                self.connection.rollback()
                logging.info("Транзакция восстановлена")
            except Exception as e:
                logging.error(f"Ошибка восстановления транзакции: {e}")

    def ensure_connection(self):
        """Восстанавливает соединение если транзакция сломана"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            logging.info("Соединение с БД активно")
        except Exception as e:
            logging.warning(f"Восстановление соединения с БД: {e}")
            if self.connection:
                self.connection.rollback()

    def connect_to_database(self):
        """ Подключение к базе данных на сервере """
        try:
            connection = psycopg.connect(
                user=user_name,
                password=user_password,
                host=host_address,
                dbname=database_name
            )
            logging.info(f"Подключено к БД: {connection}")
            return connection
        except Exception as e:
            logging.error(f"Ошибка подключения к БД: {e}")
            return None

    def check_user_login_password(self, user_login: str, user_password: str) -> bool:
        """
        Метод проверки наличия пользователя в БД
        :param user_login: Логин введеный пользователем
        :param user_password: Пароль ввденый пользователем
        :return: True - пользователь есть | False - пользователя нет
        """
        try:
            logging.info(f"Проверка авторизации пользователя: {user_login}")
            query = """
            select user_login, user_role
            from Client
            where user_login = %s
                and user_password = %s
            """
            existing_login = ""
            existing_user_role = ""
            with self.connection.cursor() as cursor:
                cursor.execute(query, (user_login, user_password))
                for answer in cursor.fetchall():
                    existing_login = answer[0]
                    existing_user_role = answer[1]
            
            if existing_login == "":
                logging.warning(f"Пользователь {user_login} не найден или пароль неверен")
                return False

            Storage.set_user_login(existing_login)
            Storage.set_user_role(existing_user_role)
            logging.info(f"Пользователь {user_login} успешно авторизован, роль: {existing_user_role}")
            return True
        except Exception as e:
            logging.error(f"Ошибка проверки пользователя: {e}")
            return False

    def take_user_data(self) -> dict:
        """
        Метод получения информации по пользовтелю
        :return: Словарь с данными
        """
        try:
            user_login = Storage.get_user_login()
            logging.info(f"Получение данных пользователя: {user_login}")
            query = """
            select *
            from Client
            where user_login = %s
            """
            result = dict()
            with self.connection.cursor() as cursor:
                cursor.execute(query, (user_login,))
                for answer in cursor.fetchall():
                    result["user_role"] = answer[0]
                    result["user_name"] = answer[1]
                    result["user_login"] = answer[2]
                    result["user_password"] = answer[3]

            if result == dict():
                logging.info("Вход выполнен как гость")
                result["user_role"] = "Гость"
                result["user_name"] = "Аккаунт Гостя"
            logging.info(f"Данные пользователя получены: {result['user_name']}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения данных пользователя: {e}")
            return {"user_role": "Гость", "user_name": "Аккаунт Гостя"}

    def get_all_items(self):
        """
        Метод получения списка всех товаров
        :return: list(dict())
        """
        try:
            logging.info("Запрос на получение всех товаров из БД")
            query = """
            select *
            from Items
            """
            result = []
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                for answer in cursor.fetchall():
                    picture = answer[11]
                    if picture == "" or picture is None:
                        picture = "picture.png"
                    result.append(
                        {
                            "id": answer[0],
                            "article": answer[1],
                            "name": answer[2],
                            "edinica": answer[3],
                            "cost": answer[4],
                            "deliveryman": answer[5],
                            "creator": answer[6],
                            "category": answer[7],
                            "sale": answer[8],
                            "count": answer[9],
                            "information": answer[10],
                            "picture": picture,
                        }
                    )
            logging.info(f"Получено товаров из БД: {len(result)}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения товаров: {e}")
            return []

    def search_and_filter_items(self,
                                search_text: str = "",
                                company_filter: str = "",
                                sort_by_count: bool = False,
                                sort_ascending: bool = True):
        try:
            logging.info(f"Поиск товаров: текст='{search_text}', фильтр='{company_filter}', сортировка по кол-ву={sort_by_count}")
            query = """
                SELECT 
                    item_id, item_article, item_name, item_edinica, item_cost,
                    item_deliveryman, item_creator, item_category,
                    item_sale, item_count, item_information, item_picture
                FROM Items
                WHERE 1=1
            """
            params = []

            if search_text:
                search_words = search_text.split()
                conditions = []
                for word in search_words:
                    if word.strip():
                        word_conditions = [
                            "item_article ILIKE %s",
                            "item_name ILIKE %s", 
                            "item_edinica ILIKE %s",
                            "item_deliveryman ILIKE %s",
                            "item_creator ILIKE %s",
                            "item_category ILIKE %s",
                            "item_information ILIKE %s"
                        ]
                        conditions.append(f"({' OR '.join(word_conditions)})")
                        params.extend([f"%{word}%"] * 7)
                
                if conditions:
                    query += f" AND ({' AND '.join(conditions)})"

            if company_filter and company_filter != "Все поставщики":
                query += " AND item_deliveryman = %s"
                params.append(company_filter)

            if sort_by_count:
                if sort_ascending:
                    query += " ORDER BY item_count ASC"
                else:
                    query += " ORDER BY item_count DESC"
            else:
                query += " ORDER BY item_name"

            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

            result = []
            for answer in rows:
                picture = answer[11] or "picture.png"
                result.append({
                    "id": answer[0],
                    "article": answer[1],
                    "name": answer[2],
                    "edinica": answer[3],
                    "cost": answer[4],
                    "deliveryman": answer[5],
                    "creator": answer[6],
                    "category": answer[7],
                    "sale": answer[8],
                    "count": answer[9],
                    "information": answer[10],
                    "picture": picture,
                })
            logging.info(f"Поиск завершен, найдено товаров: {len(result)}")
            return result
        except Exception as e:
            logging.error(f"Ошибка поиска товаров: {e}")
            return []

    def take_all_deliveryman(self):
        """
        Метод получения всех поставщиков
        :return: Список поставщиков
        """
        try:
            logging.info("Запрос всех поставщиков из БД")
            result = ["Все поставщики"]
            with self.connection.cursor() as cursor:
                cursor.execute("""
                SELECT DISTINCT item_deliveryman
                FROM Items
                ORDER BY item_deliveryman
                """)
                for answer in cursor.fetchall():
                    result.append(answer[0])
            logging.info(f"Получено поставщиков: {len(result)-1}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения поставщиков: {e}")
            return ["Все поставщики"]

    def take_item_single_info(self):
        """
        Метод получения информации о конкретном товаре
        :return: dict()
        """
        try:
            item_id = Storage.get_item_id()
            logging.info(f"Запрос данных товара ID: {item_id}")
            query = """
            select *
            from Items
            where item_id = %s
            """
            result = dict()
            with self.connection.cursor() as cursor:
                cursor.execute(query, (item_id,))
                for answer in cursor.fetchall():
                    result = {
                        "id": answer[0],
                        "article": answer[1],
                        "name": answer[2],
                        "edinica": answer[3],
                        "cost": float(answer[4]) if answer[4] else 0.0,
                        "deliveryman": answer[5],
                        "creator": answer[6],
                        "category": answer[7],
                        "sale": answer[8],
                        "count": answer[9],
                        "information": answer[10],
                        "picture": answer[11] or ""
                    }
            logging.info(f"Данные товара получены: {result.get('name', 'Неизвестно')}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения данных товара: {e}")
            self.connection.rollback()
            return {}

    def update_card_picture(self, picture_name: str, user_input_data: list):
        """
        Обновление фотографии товара
        :param picture_name: Новое имя товара
        :param user_input_data: Данные от ввода пользователя
        :return: Bool
        """
        try:
            item_id = Storage.get_item_id()
            logging.info(f"Обновление товара ID: {item_id}, фото: {picture_name}")
            self.connection.rollback()
            
            query = """
                UPDATE Items
                SET item_picture = %s,
                item_article = %s,
                item_name = %s,
                item_edinica = %s,
                item_cost = %s,
                item_deliveryman = %s,
                item_creator = %s,
                item_category = %s,
                item_sale = %s,
                item_count = %s,
                item_information = %s
                WHERE item_id = %s
            """
            
            if len(user_input_data) != 10:
                logging.error(f"ОШИБКА: ожидалось 10 параметров, получено {len(user_input_data)}")
                return False
            
            params = [
                picture_name,
                user_input_data[0],
                user_input_data[1],
                user_input_data[2],
                float(user_input_data[3]) if user_input_data[3] else 0.0,
                user_input_data[4],
                user_input_data[5],
                user_input_data[6],
                int(user_input_data[7]) if user_input_data[7] else 0,
                int(user_input_data[8]) if user_input_data[8] else 0,
                user_input_data[9],
                item_id
            ]
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, tuple(params))
                self.connection.commit()
            
            logging.info(f"Товар успешно обновлен в БД: ID={item_id}, фото={picture_name}")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка обновления товара: {e}")
            traceback.print_exc()
            self.connection.rollback()
            return False

    def create_new_card(self, user_input: list, picture_name: str):
        """
        Метод создания нового товара
        :param user_input: Ввод пользователя
        :param picture_name: Название для фото
        :return: bool
        """
        try:
            logging.info(f"Создание нового товара: артикул={user_input[0]}, фото={picture_name}")
            query = """
            insert into Items (
            item_article,
            item_name,
            item_edinica,
            item_cost,
            item_deliveryman,
            item_creator,
            item_category,
            item_sale,
            item_count,
            item_information,
            item_picture)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            with self.connection.cursor() as cursor:
                cursor.execute(query, tuple(map(str, user_input)) + (picture_name,))
                self.connection.commit()
            logging.info("Товар успешно создан в БД")
            return True
        except Exception as e:
            logging.error(f"Ошибка создания товара: {e}")
            self.connection.rollback()
            return False

    def delete_item(self, item_article: str):
        """
        Метод для удаления товара из таблицы
        :return: bool
        """
        try:
            item_id = Storage.get_item_id()
            logging.info(f"Запрос на удаление товара: ID={item_id}, артикул={item_article}")
            
            with self.connection.cursor() as cursor:
                cursor.execute("""
                SELECT COUNT(*) FROM OrderItems WHERE product_article = %s
                """, (item_article,))
                
                count = cursor.fetchone()[0]
                if count != 0:
                    logging.warning(f"Товар {item_article} используется в {count} заказах, удаление отменено")
                    return False
                
                cursor.execute("""
                        delete 
                        FROM Items
                        WHERE item_id = %s
                        """, (item_id,))
                self.connection.commit()
            logging.info(f"Товар успешно удален из БД: ID={item_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления товара: {e}")
            self.connection.rollback()
            return False

    def take_all_text_data_for_combo_box(self, type_of_data: str):
        """
        Метод для получения списка строк для Выпадающего списка
        :param type_of_data: Наименование колонки для получения данных
        :return: list()
        """
        try:
            logging.info(f"Получение данных для комбобокса: {type_of_data}")
            column_name = "*"
            if type_of_data == "category":
                column_name = "item_category"
            elif type_of_data == "deliveryman":
                column_name = "item_deliveryman"
            elif type_of_data == "creator":
                column_name = "item_creator"

            query = f"""
            select DISTINCT {column_name}
            from Items
            where {column_name} is not null and {column_name} != ''
            order by {column_name}
            """

            result = []
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                for answer in cursor.fetchall():
                    result.append(str(answer[0]))

            logging.info(f"Получено значений для комбобокса {type_of_data}: {len(result)}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения данных для комбобокса: {e}")
            return []

    def take_all_orders_rows(self):
        """Получает все заказы для отображения в списке"""
        try:
            logging.info("Запрос всех заказов из БД")
            query = """
            SELECT 
                order_id as id,
                order_status as status,
                order_pvz_id_fk as pvz,
                order_create_date as create_date,
                order_delivery_date as delivery_date,
                order_client_name as client_name
            FROM orders
            ORDER BY order_id
            """
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            
            result = []
            for row in rows:
                result.append({
                    'id': row[0],
                    'status': row[1],
                    'pvz': row[2],
                    'create_date': row[3],
                    'delivery_date': row[4],
                    'client_name': row[5]
                })
            
            logging.info(f"Успешно получено заказов: {len(result)}")
            return result
            
        except Exception as e:
            logging.error(f"Ошибка получения всех заказов: {e}")
            return []

    def take_single_order_data(self):
        """Получает данные текущего выбранного заказа"""
        try:
            order_id = Storage.get_order_id()
            if not order_id:
                logging.warning("Нет order_id в Storage")
                return {}
                
            return self.get_order_by_id(order_id)
            
        except Exception as e:
            logging.error(f"Ошибка в take_single_order_data: {e}")
            return {}

    def take_pvz_address(self, pvz_id):
        """Получает адрес ПВЗ по ID"""
        try:
            logging.info(f"Запрос адреса ПВЗ ID: {pvz_id}")
            query = "SELECT pvz_address FROM pvz WHERE pvz_id = %s"
            with self.connection.cursor() as cursor:
                cursor.execute(query, (pvz_id,))
                result = cursor.fetchone()
            
            if result:
                logging.info(f"Адрес ПВЗ найден: {result[0]}")
                return result[0]
            else:
                logging.warning(f"Адрес ПВЗ не найден: {pvz_id}")
                return "Адрес не найден"
        except Exception as e:
            logging.error(f"Ошибка получения адреса ПВЗ: {e}")
            return "Ошибка загрузки адреса"

    def take_all_pvz_addresses(self):
        """Получает все адреса ПВЗ для выпадающего списка"""
        try:
            logging.info("Запрос всех адресов ПВЗ")
            query = "SELECT pvz_id, pvz_address FROM pvz ORDER BY pvz_id"
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            
            result = [f"{row[0]} | {row[1]}" for row in rows]
            logging.info(f"Получено адресов ПВЗ: {len(result)}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения адресов ПВЗ: {e}")
            return []

    def take_all_statuses(self):
        """
        Метод получения всех вариантов статуса заказа
        :return: list()
        """
        try:
            logging.info("Запрос всех статусов заказов")
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    select DISTINCT order_status
                    from Orders;
                    """
                )
                result = [str(i[0]) for i in cursor.fetchall()]
            logging.info(f"Получено статусов заказов: {len(result)}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения статусов: {e}")
            return ["Новый", "Завершен"]

    def get_order_items(self, order_id):
        """Получает товары заказа"""
        try:
            logging.info(f"Запрос товаров заказа ID: {order_id}")
            query = """
            SELECT 
                oi.product_article as article,
                oi.quantity,
                i.item_name as name
            FROM orderitems oi
            LEFT JOIN items i ON oi.product_article = i.item_article
            WHERE oi.order_id = %s
            """
            with self.connection.cursor() as cursor:
                cursor.execute(query, (order_id,))
                rows = cursor.fetchall()
            
            result = []
            for row in rows:
                result.append({
                    'article': row[0],
                    'quantity': row[1],
                    'name': row[2] if row[2] else 'Товар не найден'
                })
            
            logging.info(f"Получено товаров для заказа {order_id}: {len(result)}")
            return result
            
        except Exception as e:
            logging.error(f"Ошибка получения товаров заказа: {e}")
            return []

    def get_order_items_with_prices(self, order_id):
        """Получает товары заказа с ценами"""
        try:
            logging.info(f"Запрос товаров заказа с ценами ID: {order_id}")
            query = """
            SELECT 
                oi.product_article as article,
                oi.quantity,
                i.item_name as name,
                i.item_cost as price
            FROM orderitems oi
            LEFT JOIN items i ON oi.product_article = i.item_article
            WHERE oi.order_id = %s
            """
            with self.connection.cursor() as cursor:
                cursor.execute(query, (order_id,))
                rows = cursor.fetchall()
            
            result = []
            for row in rows:
                result.append({
                    'article': row[0],
                    'quantity': row[1],
                    'name': row[2] if row[2] else 'Товар не найден',
                    'price': row[3] if row[3] else 0
                })
            
            logging.info(f"Получено товаров с ценами: {len(result)}")
            return result
            
        except Exception as e:
            logging.error(f"Ошибка получения товаров заказа с ценами: {e}")
            return []

    def check_product_in_orders(self, product_article):
        """Проверяет, используется ли товар в заказах"""
        try:
            logging.info(f"Проверка использования товара в заказах: {product_article}")
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM OrderItems WHERE product_article = %s", (product_article,))
                count = cursor.fetchone()[0]
            logging.info(f"Товар {product_article} используется в {count} заказах")
            return count > 0
        except Exception as e:
            logging.error(f"Ошибка проверки товара в заказах: {e}")
            return False

    def create_new_order(self, order_data):
        """Создает новый заказ в БД"""
        try:
            logging.info(f"Создание нового заказа: ПВЗ={order_data['pvz_id']}, статус={order_data['status']}")
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(order_id), 0) + 1 FROM Orders")
                next_order_id = cursor.fetchone()[0]
                order_article = f"ORD{next_order_id:06d}"
                
                order_query = """
                INSERT INTO Orders (order_create_date, order_delivery_date, order_pvz_id_fk,
                                    order_client_name, order_code, order_status)
                VALUES (CURRENT_DATE, %s, %s, %s, %s, %s)
                RETURNING order_id
                """
                
                cursor.execute(order_query, (
                    order_data['delivery_date'],
                    order_data['pvz_id'],
                    order_data['client_name'], 
                    order_data['code'],
                    order_data['status']
                ))
                
                order_id = cursor.fetchone()[0]
                logging.info(f"Создан заказ с ID: {order_id}")
                
                items_query = """
                INSERT INTO OrderItems (order_id, product_article, quantity)
                VALUES (%s, %s, %s)
                """
                
                update_query = """
                UPDATE Items 
                SET item_count = item_count - %s 
                WHERE item_article = %s
                """
                
                for item in order_data['items']:
                    cursor.execute(items_query, (order_id, item['article'], item['quantity']))
                    logging.info(f"Добавлен товар {item['article']} x{item['quantity']}")
                    cursor.execute(update_query, (item['quantity'], item['article']))
                
                self.connection.commit()
            
            logging.info(f"Заказ успешно создан! ID: {order_id}, товаров: {len(order_data['items'])}")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка создания заказа: {e}")
            traceback.print_exc()
            self.connection.rollback()
            return False

    def update_order_data(self, order_data):
        """Обновляет данные заказа"""
        try:
            logging.info(f"Обновление заказа ID: {order_data['id']}")
            query = """
            UPDATE orders 
            SET 
                order_pvz_id_fk = %s,
                order_status = %s,
                order_delivery_date = %s
            WHERE order_id = %s
            """
            with self.connection.cursor() as cursor:
                cursor.execute(query, (
                    order_data['pvz_id'],
                    order_data['status'],
                    order_data['delivery_date'],
                    order_data['id']
                ))
                self.connection.commit()
            
            logging.info(f"Заказ {order_data['id']} успешно обновлен")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка обновления заказа: {e}")
            self.connection.rollback()
            return False

    def delete_order(self, order_id):
        """Удаляет заказ"""
        try:
            logging.info(f"Удаление заказа ID: {order_id}")
            with self.connection.cursor() as cursor:
                cursor.execute("""
                SELECT product_article, quantity 
                FROM OrderItems 
                WHERE order_id = %s
                """, (order_id,))
                
                items = cursor.fetchall()
                logging.info(f"Товаров для возврата на склад: {len(items)}")
                for article, quantity in items:
                    cursor.execute("""
                    UPDATE Items 
                    SET item_count = item_count + %s 
                    WHERE item_article = %s
                    """, (quantity, article))
                
                cursor.execute("DELETE FROM Orders WHERE order_id = %s", (order_id,))
                self.connection.commit()
                
            logging.info(f"Заказ {order_id} успешно удален")
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления заказа: {e}")
            self.connection.rollback()
            return False

    def get_order_by_id(self, order_id):
        """Получает данные конкретного заказа по ID"""
        try:
            logging.info(f"Запрос данных заказа ID: {order_id}")
            query = """
            SELECT 
                order_id as id,
                order_create_date as create_date,
                order_delivery_date as delivery_date,
                order_pvz_id_fk as pvz,
                order_status as status,
                order_client_name as client_name,
                order_code as code
            FROM orders
            WHERE order_id = %s
            """
            with self.connection.cursor() as cursor:
                cursor.execute(query, (order_id,))
                result = cursor.fetchone()
            
            if result:
                logging.info(f"Найден заказ: ID={result[0]}, статус={result[4]}")
                return {
                    'id': result[0],
                    'create_date': result[1],
                    'delivery_date': result[2],
                    'pvz': result[3],
                    'status': result[4],
                    'client_name': result[5],
                    'code': result[6]
                }
            else:
                logging.warning(f"Заказ с ID {order_id} не найден")
                return None
                
        except Exception as e:
            logging.error(f"Ошибка получения заказа по ID: {e}")
            traceback.print_exc()
            return None