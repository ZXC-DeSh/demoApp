import pandas as pd
import psycopg
import os
from config import *
from datetime import datetime

def get_file_path(filename):
    """Получение относительного пути к файлу"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "EXCEL", filename)

def clear_tables(conn):
    """Очищает все таблицы перед импортом"""
    cursor = conn.cursor()
    
    # Очищаем в правильном порядке (с учетом внешних ключей)
    tables = ['OrderItems', 'Orders', 'Items', 'Client', 'PVZ']
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"Очищена таблица: {table}")
        except Exception as e:
            print(f"Ошибка очистки {table}: {e}")
    
    conn.commit()
    cursor.close()
    print("Все таблицы очищены!")

def import_clients(conn):
    query = """
    INSERT INTO Client (user_role, user_name, user_login, user_password)
    VALUES (%s, %s, %s, %s);
    """
    data_frame = pd.read_excel(get_file_path("user_import.xlsx"))
    
    # Отладочная информация - посмотрим реальные названия колонок
    print("Колонки в user_import.xlsx:")
    print(data_frame.columns.tolist())
    
    cursor = conn.cursor()
    
    for row in data_frame.itertuples():
        # Используем индексы вместо имен колонок
        # Структура: Index, Роль сотрудника, ФИО, Логин, Пароль
        values = (row[1], row[2], row[3], row[4])  # Индексы с 1, т.к. 0 - это Index
        print(f"Импортируем: {values}")
        cursor.execute(query, values)
    
    conn.commit()
    cursor.close()
    print("Клиенты импортированы!")

def import_items(conn):
    query = """
    INSERT INTO Items (
        item_article, item_name, item_edinica, item_cost, 
        item_deliveryman, item_creator, item_category, 
        item_sale, item_count, item_information, item_picture
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    data_frame = pd.read_excel(get_file_path("Tovar.xlsx"))
    
    print("Колонки в Tovar.xlsx:")
    print(data_frame.columns.tolist())
    
    cursor = conn.cursor()
    
    for row in data_frame.itertuples():
        picture = str(row[11]) if pd.notna(row[11]) and str(row[11]) != "nan" else ""
        
        values = (
            row[1],  # Артикул
            row[2],  # Наименование товара
            row[3],  # Единица измерения
            float(row[4]),  # Цена
            row[5],  # Поставщик
            row[6],  # Производитель
            row[7],  # Категория товара
            int(row[8]),  # Действующая скидка
            int(row[9]),  # Кол-во на складе
            row[10],  # Описание товара
            picture
        )
        print(f"Импортируем товар: {values[0]} - {values[1]}")
        cursor.execute(query, values)
    
    conn.commit()
    cursor.close()
    print("Товары импортированы!")

def import_pvz(conn):
    query = """
    INSERT INTO PVZ (pvz_address)
    VALUES (%s);
    """
    data_frame = pd.read_excel(get_file_path("Пункты выдачи_import.xlsx"))
    
    print("Колонки в Пункты выдачи_import.xlsx:")
    print(data_frame.columns.tolist())
    print(f"Найдено записей: {len(data_frame)}")
    
    cursor = conn.cursor()
    
    success_count = 0
    for row in data_frame.itertuples():
        try:
            values = (row[1],)  # Адрес - 1й столбец
            cursor.execute(query, values)
            success_count += 1
        except Exception as e:
            print(f"Пропускаем дубликат: {row[1]}")
            continue
    
    conn.commit()
    cursor.close()
    print(f"ПВЗ импортированы! Успешно: {success_count}")

def parse_order_articles(article_string):
    """Разбирает строку с артикулами заказа на отдельные позиции"""
    items = []
    try:
        # Пример: "А112Т4, 2, F635R4, 2" -> [('А112Т4', 2), ('F635R4', 2)]
        parts = [x.strip() for x in article_string.split(',')]
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                article = parts[i]
                quantity = int(parts[i + 1])
                items.append((article, quantity))
    except Exception as e:
        print(f"Ошибка разбора артикулов: {article_string}, ошибка: {e}")
    return items

def import_orders(conn):
    # Сначала импортируем заказы
    order_query = """
    INSERT INTO Orders (
        order_create_date, order_delivery_date, order_pvz_id_fk,
        order_client_name, order_code, order_status
    ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING order_id;
    """
    
    # Затем состав заказов
    order_items_query = """
    INSERT INTO OrderItems (order_id, product_article, quantity)
    VALUES (%s, %s, %s);
    """
    
    data_frame = pd.read_excel(get_file_path("Заказ_import.xlsx"))
    
    print("Колонки в Заказ_import.xlsx:")
    print(data_frame.columns.tolist())
    
    cursor = conn.cursor()
    
    success_count = 0
    for row in data_frame.itertuples():
        try:
            # Используем индексы колонок
            # Номер заказа, Артикул заказа, Дата заказа, Дата доставки, 
            # Адрес пункта выдачи, ФИО клиента, Код для получения, Статус заказа
            
            create_date = parse_date(str(row[3]))  # Дата заказа
            delivery_date = parse_date(str(row[4]))  # Дата доставки
            
            # PVZ ID (уже должен существовать)
            pvz_id = int(row[5])  # Адрес пункта выдачи
            
            values = (
                create_date, delivery_date, pvz_id,
                row[6],  # ФИО клиента
                int(row[7]),  # Код для получения
                row[8]   # Статус заказа
            )
            
            # Вставляем заказ и получаем его ID
            cursor.execute(order_query, values)
            order_id = cursor.fetchone()[0]
            
            # Разбираем и вставляем состав заказа
            order_items = parse_order_articles(row[2])  # Артикул заказа
            for article, quantity in order_items:
                cursor.execute(order_items_query, (order_id, article, quantity))
            
            success_count += 1
            print(f"Импортирован заказ #{row[1]} с {len(order_items)} товарами")
                
        except Exception as e:
            print(f"Ошибка импорта заказа {row[1]}: {e}")
            continue
    
    conn.commit()
    cursor.close()
    print(f"Заказы импортированы! Успешно: {success_count}")

def parse_date(date_str):
    """Парсит дату из разных форматов"""
    try:
        # Пробуем разные форматы дат
        if ' ' in date_str:
            date_str = date_str.split(' ')[0]
        
        if '.' in date_str:
            return datetime.strptime(date_str, "%d.%m.%Y").date()
        elif '-' in date_str:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            # Если формат непонятен, используем текущую дату
            return datetime.now().date()
    except Exception:
        print(f"Ошибка парсинга даты: {date_str}")
        return datetime.now().date()

def main():
    connection = psycopg.connect(
        user=user_name,
        password=user_password,
        host=host_address,
        dbname=database_name
    )

    try:
        print("Начинаем импорт данных...")
        
        # Сначала очищаем таблицы
        clear_tables(connection)
        
        # Затем импортируем в правильном порядке
        import_pvz(connection)
        import_clients(connection) 
        import_items(connection)
        import_orders(connection)
        
        print("✅ Все данные успешно импортированы!")
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
    finally:
        connection.close()

if __name__ == "__main__":
    main()