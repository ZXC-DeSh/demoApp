import psycopg
from DATABASE.config import *
from StaticStorage import Storage
import logging


class DatabaseConnection:
    def __init__(self):
        """ Конструктор класса """
        logging.info("Инициализация подключения к базе данных")
        self.connection = self.connect_to_database()
        # Восстанавливаем транзакцию при инициализации
        if self.connection:
            try:
                self.connection.rollback()
                logging.info("Транзакция восстановлена")
            except Exception as e:
                logging.error(f"Ошибка восстановления транзакции: {e}")

    def ensure_connection(self):
        """Восстанавливает соединение если транзакция сломана"""
        try:
            # Пробуем выполнить простой запрос
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            logging.info("Соединение с БД активно")
        except Exception as e:
            # Если запрос не прошел, восстанавливаем соединение
            logging.warning(f"Восстановление соединения с БД: {e}")
            self.connection.rollback()

    def connect_to_database(self):
        """ Подключение к базе данных на сервере """
        try:
            # Подключение
            connection = psycopg.connect(
                user=user_name,
                password=user_password,
                host=host_address,
                dbname=database_name
            )
            logging.info(f"Подключено к БД: {connection}")
            return connection
        except Exception as e:
            # Ошибка при подключении
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
            cursor = self.connection.cursor()
            cursor.execute(query, (user_login, user_password))
            existing_login = ""
            existing_user_role = ""
            for answer in cursor.fetchall():
                existing_login = answer[0]
                existing_user_role = answer[1]
            cursor.close()
            
            if existing_login == "":
                # Не найдено совпадений Логина И Пароля - Аккаунт не существует
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
            cursor = self.connection.cursor()
            cursor.execute(query, (user_login,))
            result = dict()
            for answer in cursor.fetchall():
                result["user_role"] = answer[0]
                result["user_name"] = answer[1]
                result["user_login"] = answer[2]
                result["user_password"] = answer[3]
            cursor.close()

            if result == dict():
                # Если ответ из БД - пустой, значит входил гость
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
            cursor = self.connection.cursor()
            cursor.execute(query)
            for answer in cursor.fetchall():
                picture = answer[11]
                if picture == "" or picture is None:
                    picture = "picture.png"
                result.append(
                    # Добавление словаря для каждого товара в список
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
            cursor.close()
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

            # Поиск по тексту (регистронезависимо в PostgreSQL — ILIKE)
            if search_text:
                # Разбиваем строку поиска на отдельные слова
                search_words = search_text.split()
                
                conditions = []
                # Для каждого слова создаем условия поиска по всем полям
                for word in search_words:
                    if word.strip():  # Проверяем, что слово не пустое
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
                        # Добавляем слово с % для каждого поля (7 полей)
                        params.extend([f"%{word}%"] * 7)
                
                if conditions:
                    # Объединяем условия через AND (все слова должны встречаться где-то в записи)
                    query += f" AND ({' AND '.join(conditions)})"

            # Фильтр по поставщику
            if company_filter and company_filter != "Все поставщики":
                query += " AND item_deliveryman = %s"
                params.append(company_filter)

            # Сортировка
            if sort_by_count:
                if sort_ascending:
                    query += " ORDER BY item_count ASC"  # по возрастанию
                else:
                    query += " ORDER BY item_count DESC"  # по убыванию
            else:
                query += " ORDER BY item_name"  # по умолчанию — по названию

            cursor = self.connection.cursor()
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
            cursor.close()
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
            cursor = self.connection.cursor()
            cursor.execute("""
            SELECT DISTINCT item_deliveryman
            FROM Items
            ORDER BY item_deliveryman
            """)

            result = ["Все поставщики"]
            for answer in cursor.fetchall():
                result.append(answer[0])
            cursor.close()
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
            cursor = self.connection.cursor()
            cursor.execute(query, (item_id,))
            result = dict()
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
            cursor.close()
            logging.info(f"Данные товара получены: {result.get('name', 'Неизвестно')}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения данных товара: {e}")
            # В случае ошибки сбрасываем транзакцию
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
            
            # Восстанавливаем соединение
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
            
            # Проверяем количество параметров
            if len(user_input_data) != 10:
                logging.error(f"ОШИБКА: ожидалось 10 параметров, получено {len(user_input_data)}")
                return False
            
            # Подготавливаем параметры
            params = [
                picture_name,  # item_picture
                user_input_data[0],  # item_article
                user_input_data[1],  # item_name
                user_input_data[2],  # item_edinica (unit)
                float(user_input_data[3]) if user_input_data[3] else 0.0,  # item_cost
                user_input_data[4],  # item_deliveryman
                user_input_data[5],  # item_creator
                user_input_data[6],  # item_category
                int(user_input_data[7]) if user_input_data[7] else 0,  # item_sale
                int(user_input_data[8]) if user_input_data[8] else 0,  # item_count
                user_input_data[9],  # item_information
                item_id  # WHERE item_id
            ]
            
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(params))
            self.connection.commit()
            cursor.close()
            
            logging.info(f"Товар успешно обновлен в БД: ID={item_id}, фото={picture_name}")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка обновления товара: {e}")
            import traceback
            traceback.print_exc()
            self.connection.rollback()
            return False

    def create_new_card(self,
                        user_input: list,
                        picture_name: str):
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
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(map(str, user_input)) + (picture_name,))
            self.connection.commit()
            cursor.close()
            logging.info("Товар успешно создан в БД")
            return True
        except Exception as e:
            logging.error(f"Ошибка создания товара: {e}")
            self.connection.rollback()
            return False

    def delete_item(self,
                    item_article: str):
        """
        Метод для удаления товара из таблицы
        :return: bool
        """
        try:
            item_id = Storage.get_item_id()
            logging.info(f"Запрос на удаление товара: ID={item_id}, артикул={item_article}")
            cursor = self.connection.cursor()
            # Проверка, что товара нет в заказах
            cursor.execute("""
            SELECT COUNT(*) FROM OrderItems WHERE product_article = %s
            """, (item_article,))
            
            count = cursor.fetchone()[0]
            if count != 0:
                cursor.close()
                logging.warning(f"Товар {item_article} используется в {count} заказах, удаление отменено")
                return False
            
            # Если в ответе от бд есть хоть 1 элемент - отклонение запроса
            # Запуск удаления элемента
            cursor.execute("""
                    delete 
                    FROM Items
                    WHERE item_id = %s
                    """, (item_id,))
            self.connection.commit()
            cursor.close()
            logging.info(f"Товар успешно удален из БД: ID={item_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления товара: {e}")
            self.connection.rollback()
            return False

    def take_all_text_data_for_combo_box(self,
                                         type_of_data: str):
        """
        Метод для получения списка строк для Выпадающего списка
        :param type_of_data: Наименование колонки для получения данных
        :return: list()
        """
        try:
            logging.info(f"Получение данных для комбобокса: {type_of_data}")
            # По умолчанию - выбираем все колонки
            # Но 100% будет 1 из вариантов Условного Опператора
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

            cursor = self.connection.cursor()
            cursor.execute(query)

            result = []

            for answer in cursor.fetchall():
                result.append(str(answer[0]))

            cursor.close()
            logging.info(f"Получено значений для комбобокса {type_of_data}: {len(result)}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения данных для комбобокса: {e}")
            return []

    def take_all_orders_rows(self):
        """Получает все заказы для отображения в списке"""
        try:
            logging.info("Запрос всех заказов из БД")
            cursor = self.connection.cursor()
            
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
            
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
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
            cursor = self.connection.cursor()
            query = "SELECT pvz_address FROM pvz WHERE pvz_id = %s"
            cursor.execute(query, (pvz_id,))
            result = cursor.fetchone()
            cursor.close()
            
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
            cursor = self.connection.cursor()
            query = "SELECT pvz_id, pvz_address FROM pvz ORDER BY pvz_id"
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            # Формируем строки в формате "ID | Адрес"
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
            cursor = self.connection.cursor()
            cursor.execute(
                """
                select DISTINCT order_status
                from Orders;
                """
            )
            result = [str(i[0]) for i in cursor.fetchall()]
            cursor.close()
            logging.info(f"Получено статусов заказов: {len(result)}")
            return result
        except Exception as e:
            logging.error(f"Ошибка получения статусов: {e}")
            return ["Новый", "Завершен"]

    def get_order_items(self, order_id):
        """Получает товары заказа"""
        try:
            logging.info(f"Запрос товаров заказа ID: {order_id}")
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                oi.product_article as article,
                oi.quantity,
                i.item_name as name
            FROM orderitems oi
            LEFT JOIN items i ON oi.product_article = i.item_article
            WHERE oi.order_id = %s
            """
            
            cursor.execute(query, (order_id,))
            rows = cursor.fetchall()
            cursor.close()
            
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
            cursor = self.connection.cursor()
            
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
            
            cursor.execute(query, (order_id,))
            rows = cursor.fetchall()
            cursor.close()
            
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
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM OrderItems WHERE product_article = %s", (product_article,))
            count = cursor.fetchone()[0]
            cursor.close()
            logging.info(f"Товар {product_article} используется в {count} заказах")
            return count > 0
        except Exception as e:
            logging.error(f"Ошибка проверки товара в заказах: {e}")
            return False

    def create_new_order(self, order_data):
        """Создает новый заказ в БД"""
        try:
            logging.info(f"Создание нового заказа: ПВЗ={order_data['pvz_id']}, статус={order_data['status']}")
            cursor = self.connection.cursor()
            
            # Генерируем артикул заказа на основе ID
            cursor.execute("SELECT COALESCE(MAX(order_id), 0) + 1 FROM Orders")
            next_order_id = cursor.fetchone()[0]
            order_article = f"ORD{next_order_id:06d}"
            
            # Вставляем заказ
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
            
            # Вставляем товары заказа
            items_query = """
            INSERT INTO OrderItems (order_id, product_article, quantity)
            VALUES (%s, %s, %s)
            """
            
            for item in order_data['items']:
                cursor.execute(items_query, (order_id, item['article'], item['quantity']))
                logging.info(f"Добавлен товар {item['article']} x{item['quantity']}")
                
                # Уменьшаем количество товара на складе
                update_query = """
                UPDATE Items 
                SET item_count = item_count - %s 
                WHERE item_article = %s
                """
                cursor.execute(update_query, (item['quantity'], item['article']))
            
            self.connection.commit()
            cursor.close()
            
            logging.info(f"Заказ успешно создан! ID: {order_id}, товаров: {len(order_data['items'])}")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка создания заказа: {e}")
            import traceback
            traceback.print_exc()
            self.connection.rollback()
            return False

    def update_order_data(self, order_data):
        """Обновляет данные заказа"""
        try:
            logging.info(f"Обновление заказа ID: {order_data['id']}")
            cursor = self.connection.cursor()
            
            query = """
            UPDATE orders 
            SET 
                order_pvz_id_fk = %s,
                order_status = %s,
                order_delivery_date = %s
            WHERE order_id = %s
            """
            
            cursor.execute(query, (
                order_data['pvz_id'],
                order_data['status'],
                order_data['delivery_date'],
                order_data['id']
            ))
            
            self.connection.commit()
            cursor.close()
            
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
            cursor = self.connection.cursor()
            
            # Сначала возвращаем товары на склад
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
            
            # Удаляем заказ (каскадно удалятся OrderItems)
            cursor.execute("DELETE FROM Orders WHERE order_id = %s", (order_id,))
            
            self.connection.commit()
            cursor.close()
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

            cursor = self.connection.cursor()

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
            
            cursor.execute(query, (order_id,))
            result = cursor.fetchone()
            cursor.close()
            
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
            import traceback
            traceback.print_exc()
            return None