import psycopg
from DATABASE.config import *
from StaticStorage import Storage


class DatabaseConnection:
    def __init__(self):
        """ Конструктор класса """
        self.connection = self.connect_to_database()
        # Восстанавливаем транзакцию при инициализации
        if self.connection:
            try:
                self.connection.rollback()
            except:
                pass

    def ensure_connection(self):
        """Восстанавливает соединение если транзакция сломана"""
        try:
            # Пробуем выполнить простой запрос
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        except Exception:
            # Если запрос не прошел, восстанавливаем соединение
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
            print(f"Подключено! {connection}")
            return connection
        except Exception as e:
            # Ошибка при подключении
            print(e)
            return None

    def check_user_login_password(self,
                                  user_login: str,
                                  user_password: str) -> bool:
        """
        Метод проверки наличия пользователя в БД
        :param user_login: Логин введеный пользователем
        :param user_password: Пароль ввденый пользователем
        :return: True - пользователь есть | False - пользователя нет
        """
        try:
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
                return False

            # Совпадения найдены
            # Добавление активного логина в статический класс
            Storage().set_user_login(existing_login)
            Storage().set_user_role(existing_user_role)
            return True
        except Exception as e:
            print(f"Ошибка проверки пользователя: {e}")
            return False

    def take_user_data(self) -> dict:
        """
        Метод получения информации по пользовтелю
        :return: Словарь с данными
        """
        try:
            query = """
            select *
            from Client
            where user_login = %s
            """
            cursor = self.connection.cursor()
            cursor.execute(query, (Storage().get_user_login(),))
            result = dict()
            for answer in cursor.fetchall():
                result["user_role"] = answer[0]
                result["user_name"] = answer[1]
                result["user_login"] = answer[2]
                result["user_password"] = answer[3]
            cursor.close()

            if result == dict():
                # Если ответ из БД - пустой, значит входил гость
                print("NO one")
                result["user_role"] = "Гость"
                result["user_name"] = "Аккаунт Гостя"
            return result
        except Exception as e:
            print(f"Ошибка получения данных пользователя: {e}")
            return {"user_role": "Гость", "user_name": "Аккаунт Гостя"}

    def get_all_items(self):
        """
        Метод получения списка всех товаров
        :return: list(dict())
        """
        try:
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
            return result
        except Exception as e:
            print(f"Ошибка получения товаров: {e}")
            return []

    def search_and_filter_items(self,
        search_text: str = "",
        company_filter: str = "",
        sort_by_count: bool = False,
        sort_ascending: bool = True):
        try:
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
            return result
        except Exception as e:
            print(f"Ошибка поиска товаров: {e}")
            return []

    def take_all_deliveryman(self):
        """
        Метод получения всех поставщиков
        :return: Список поставщиков
        """
        try:
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
            return result
        except Exception as e:
            print(f"Ошибка получения поставщиков: {e}")
            return ["Все поставщики"]

    def take_item_single_info(self):
        """
        Метод получения информации о конкретном товаре
        :return: dict()
        """
        try:
            query = """
            select *
            from Items
            where item_id = %s
            """
            cursor = self.connection.cursor()
            cursor.execute(query, (Storage.get_item_id(),))
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
            return result
        except Exception as e:
            print(f"Ошибка получения данных товара: {e}")
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
                print(f"ОШИБКА: ожидалось 10 параметров, получено {len(user_input_data)}")
                print(f"user_input_data: {user_input_data}")
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
                Storage.get_item_id()  # WHERE item_id
            ]
            
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(params))
            self.connection.commit()
            cursor.close()
            
            print(f"Товар успешно обновлен в БД: ID={Storage.get_item_id()}")
            print(f"Новое имя файла: {picture_name}")
            return True
            
        except Exception as e:
            print(f"Ошибка обновления товара: {e}")
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
            return True
        except Exception as e:
            print("Error:", e)
            self.connection.rollback()
            return False

    def delete_item(self,
                    item_article: str):
        """
        Метод для удаления товара из таблицы
        :return: bool
        """
        try:
            cursor = self.connection.cursor()
            # Проверка, что товара нет в заказах
            cursor.execute("""
            SELECT COUNT(*) FROM OrderItems WHERE product_article = %s
            """, (item_article,))
            
            if cursor.fetchone()[0] != 0:
                cursor.close()
                return False
            
            # Если в ответе от бд есть хоть 1 элемент - отклонение запроса
            # Запуск удаления элемента
            cursor.execute("""
                    delete 
                    FROM Items
                    WHERE item_id = %s
                    """, (Storage.get_item_id(),))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Ошибка удаления товара: {e}")
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
            return result
        except Exception as e:
            print(f"Ошибка получения данных для комбобокса: {e}")
            return []

    def take_all_orders_rows(self):
        """
        Метод получения списка товаров из Таблицы Orders
        :return: [dict()]
        """
        try:
            # Восстанавливаем транзакцию если она сломана
            self.connection.rollback()
            
            query = """
            SELECT order_id, order_create_date, order_delivery_date, 
                order_pvz_id_fk, order_client_name, order_code, order_status
            FROM Orders
            ORDER BY order_id;
            """

            cursor = self.connection.cursor()
            cursor.execute(query)

            result = []
            for answer in cursor.fetchall():
                result.append(
                    {
                        "id": answer[0],
                        "create_date": answer[1],
                        "delivery_date": answer[2],
                        "pvz": answer[3],
                        "client_name": answer[4],
                        "code": answer[5],
                        "status": answer[6],
                    }
                )
            cursor.close()
            print(f"Успешно получено заказов: {len(result)}")
            return result
        except Exception as e:
            print(f"Ошибка получения заказов: {e}")
            import traceback
            traceback.print_exc()
            # Всегда восстанавливаем транзакцию при ошибке
            self.connection.rollback()
            return []

    def take_single_order_data(self):
        """
        Метод получения данных о конкретном товаре
        :return: dict()
        """
        try:
            # Восстанавливаем транзакцию если она сломана
            self.connection.rollback()
            
            query = """
            SELECT order_id, order_create_date, order_delivery_date, 
                order_pvz_id_fk, order_client_name, order_code, order_status
            FROM Orders
            WHERE order_id = %s;
            """

            cursor = self.connection.cursor()
            cursor.execute(query, (Storage.get_order_id(),))

            result = {}
            for answer in cursor.fetchall():
                result = {
                    "id": answer[0],
                    "create_date": answer[1],
                    "delivery_date": answer[2],
                    "pvz": answer[3],
                    "client_name": answer[4],
                    "code": answer[5],
                    "status": answer[6],
                }

            cursor.close()
            return result
        except Exception as e:
            print(f"Ошибка получения данных заказа: {e}")
            import traceback
            traceback.print_exc()
            self.connection.rollback()
            return {}

    def take_pvz_address(self,
                         pvz_id):
        """
        Метод получения адреса ПВЗ для заказа
        :param pvz_id: id ПВЗ из заказа
        :return: string
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                select pvz_address
                from PVZ
                where pvz_id = %s
                """,
                (pvz_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            return str(result[0]) if result else "Адрес не найден"
        except Exception as e:
            print(f"Ошибка получения адреса ПВЗ: {e}")
            return "Адрес не найден"

    def take_all_pvz_addresses(self):
        """
        Метод получения всех ПВЗ для редактирования / создания нового заказа
        :return: list("1 | Старокачаловская д3к1")
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
            select *
            from PVZ
            order by pvz_id
            """)

            result = []
            for answer in cursor.fetchall():
                result.append(f"{answer[0]} | {answer[1]}")

            cursor.close()
            return result
        except Exception as e:
            print(f"Ошибка получения ПВЗ: {e}")
            return []

    def take_all_statuses(self):
        """
        Метод получения всех вариантов статуса заказа
        :return: list()
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                select DISTINCT order_status
                from Orders;
                """
            )
            result = [str(i[0]) for i in cursor.fetchall()]
            cursor.close()
            return result
        except Exception as e:
            print(f"Ошибка получения статусов: {e}")
            return ["Новый", "Завершен"]

    # Новые методы для работы с заказами
    def get_order_items(self, order_id):
        """Получает состав заказа"""
        try:
            query = """
            SELECT oi.product_article, oi.quantity, i.item_name
            FROM OrderItems oi
            LEFT JOIN Items i ON oi.product_article = i.item_article
            WHERE oi.order_id = %s
            """
            cursor = self.connection.cursor()
            cursor.execute(query, (order_id,))
            
            result = []
            for row in cursor.fetchall():
                result.append({
                    'article': row[0],
                    'quantity': row[1],
                    'name': row[2]
                })
            
            cursor.close()
            return result
        except Exception as e:
            print(f"Ошибка получения состава заказа: {e}")
            return []

    def get_order_items_with_prices(self, order_id):
        """Получает состав заказа с ценами товаров"""
        try:
            query = """
            SELECT oi.product_article, oi.quantity, i.item_name, i.item_cost
            FROM OrderItems oi
            LEFT JOIN Items i ON oi.product_article = i.item_article
            WHERE oi.order_id = %s
            ORDER BY i.item_name
            """
            cursor = self.connection.cursor()
            cursor.execute(query, (order_id,))
            
            result = []
            for row in cursor.fetchall():
                result.append({
                    'article': row[0],
                    'quantity': row[1],
                    'name': row[2],
                    'cost': float(row[3]) if row[3] else 0.0
                })
            
            cursor.close()
            return result
        except Exception as e:
            print(f"Ошибка получения состава заказа с ценами: {e}")
            return []

    def check_product_in_orders(self, product_article):
        """Проверяет, используется ли товар в заказах"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM OrderItems WHERE product_article = %s", (product_article,))
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0
        except Exception as e:
            print(f"Ошибка проверки товара в заказах: {e}")
            return False

    def create_new_order(self, order_data):
        """Создает новый заказ в БД"""
        try:
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
            print(f"Создан заказ с ID: {order_id}")
            
            # Вставляем товары заказа
            items_query = """
            INSERT INTO OrderItems (order_id, product_article, quantity)
            VALUES (%s, %s, %s)
            """
            
            for item in order_data['items']:
                cursor.execute(items_query, (order_id, item['article'], item['quantity']))
                print(f"Добавлен товар {item['article']} x{item['quantity']}")
            
            self.connection.commit()
            cursor.close()
            
            print(f"Заказ успешно создан! ID: {order_id}")
            return True
            
        except Exception as e:
            print(f"Ошибка создания заказа: {e}")
            import traceback
            traceback.print_exc()
            self.connection.rollback()
            return False

    def update_order_data(self, order_data):
        """Обновляет данные заказа"""
        try:
            cursor = self.connection.cursor()
            
            # Обновляем основную информацию заказа
            update_query = """
            UPDATE Orders 
            SET order_pvz_id_fk = %s, order_status = %s, order_code = %s, order_delivery_date = %s
            WHERE order_id = %s
            """
            
            cursor.execute(update_query, (
                order_data['pvz_id'],
                order_data['status'],
                order_data['code'], 
                order_data['delivery_date'],
                order_data['id']
            ))
            
            # Удаляем старый состав заказа
            cursor.execute("DELETE FROM OrderItems WHERE order_id = %s", (order_data['id'],))
            
            # Добавляем новый состав
            items_query = "INSERT INTO OrderItems (order_id, product_article, quantity) VALUES (%s, %s, %s)"
            for item in order_data['items']:
                cursor.execute(items_query, (order_data['id'], item['article'], item['quantity']))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Ошибка обновления заказа: {e}")
            self.connection.rollback()
            return False

    def delete_order(self, order_id):
        """Удаляет заказ"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM Orders WHERE order_id = %s", (order_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Ошибка удаления заказа: {e}")
            self.connection.rollback()
            return False
        
    def create_new_order(self, order_data):
        """Создает новый заказ в БД"""
        try:
            cursor = self.connection.cursor()
            
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
            print(f"Создан заказ с ID: {order_id}")
            
            # Вставляем товары заказа
            items_query = """
            INSERT INTO OrderItems (order_id, product_article, quantity)
            VALUES (%s, %s, %s)
            """
            
            for item in order_data['items']:
                cursor.execute(items_query, (order_id, item['article'], item['quantity']))
                print(f"Добавлен товар {item['article']} x{item['quantity']}")
            
            self.connection.commit()
            cursor.close()
            
            # Проверяем, что заказ действительно создался
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM Orders WHERE order_id = %s", (order_id,))
            count = cursor.fetchone()[0]
            cursor.close()
            print(f"Подтверждение создания заказа: {count} записей с ID {order_id}")
            
            return True
            
        except Exception as e:
            print(f"Ошибка создания заказа: {e}")
            import traceback
            traceback.print_exc()
            self.connection.rollback()
            return False
