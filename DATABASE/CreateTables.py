import psycopg
from config import *

create_table_USER = """
CREATE TABLE Client (
    user_role TEXT NOT NULL,
    user_name TEXT NOT NULL,
    user_login TEXT NOT NULL PRIMARY KEY,
    user_password TEXT NOT NULL
);
"""

create_table_ITEMS = """
CREATE TABLE Items(
    item_id SERIAL PRIMARY KEY NOT NULL,
    item_article TEXT NOT NULL,
    item_name TEXT NOT NULL,
    item_edinica TEXT NOT NULL,
    item_cost DECIMAL(10,2) NOT NULL CHECK (item_cost >= 0),
    item_deliveryman TEXT NOT NULL,
    item_creator TEXT NOT NULL,
    item_category TEXT NOT NULL,
    item_sale INTEGER NOT NULL CHECK (item_sale >= 0),
    item_count INTEGER NOT NULL CHECK (item_count >= 0),
    item_information TEXT NOT NULL,
    item_picture TEXT
);
"""

create_table_PVZ = """
CREATE TABLE PVZ(
    pvz_id SERIAL PRIMARY KEY NOT NULL,
    pvz_address TEXT NOT NULL  -- Убрал UNIQUE, т.к. в данных есть дубликаты
);
"""

create_table_ORDERS = """
CREATE TABLE Orders(
    order_id SERIAL PRIMARY KEY NOT NULL,
    order_create_date DATE NOT NULL,
    order_delivery_date DATE NOT NULL,
    order_pvz_id_fk INTEGER NOT NULL REFERENCES PVZ(pvz_id) ON UPDATE CASCADE,
    order_client_name TEXT NOT NULL,
    order_code INTEGER NOT NULL,
    order_status TEXT NOT NULL
);
"""

create_table_ORDER_ITEMS = """
CREATE TABLE OrderItems(
    order_item_id SERIAL PRIMARY KEY NOT NULL,
    order_id INTEGER NOT NULL REFERENCES Orders(order_id) ON DELETE CASCADE,
    product_article TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);
"""

def create_table(query, conn):
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()

# Удаляем существующие таблицы и создаем заново
def recreate_database():
    connection = psycopg.connect(
        user=user_name,
        password=user_password,
        host=host_address,
        dbname=database_name
    )
    
    cursor = connection.cursor()
    
    # Удаляем таблицы в обратном порядке (из-за внешних ключей)
    tables = ['OrderItems', 'Orders', 'Items', 'Client', 'PVZ']
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"Удалена таблица: {table}")
        except Exception as e:
            print(f"Ошибка удаления {table}: {e}")
    
    connection.commit()
    
    # Создаем таблицы в правильном порядке
    create_table(query=create_table_USER, conn=connection)
    create_table(query=create_table_PVZ, conn=connection)
    create_table(query=create_table_ITEMS, conn=connection)
    create_table(query=create_table_ORDERS, conn=connection)
    create_table(query=create_table_ORDER_ITEMS, conn=connection)

    print("Все таблицы успешно пересозданы!")
    connection.close()

if __name__ == "__main__":
    recreate_database()