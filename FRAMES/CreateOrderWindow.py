from PySide6.QtWidgets import (QFrame, QPushButton, QHBoxLayout, QScrollArea, QComboBox,
                               QWidget, QVBoxLayout, QLabel, QLineEdit, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from datetime import datetime
import Messages
from FRAMES import HomePageWindow, OrdersCardsWindow
from StaticStorage import Storage
from PySide6.QtGui import QPixmap
import os

class CreateOrderFrame(QFrame):
    def __init__(self, controller):
        """
        Конструктор класса создания заказа
        :param controller: "self" из класса MainApplicationClass
        """
        super().__init__()
        self.controller = controller
        self.database = controller.db
        
        # Данные заказа
        self.order_items = []  # Список товаров в заказе: [{'article': '', 'name': '', 'quantity': 1, 'available': 0}]
        self.available_products = []  # Список доступных товаров
        
        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        """Генерация интерфейса"""
        # Шапка с кнопкой назад и ФИО
        header_widget = QWidget()
        header_widget.setObjectName("header_widget")
        header_widget_hbox = QHBoxLayout(header_widget)

        # Кнопка "Назад"
        back_header_btn = QPushButton("< Назад")
        back_header_btn.setFixedWidth(150)
        back_header_btn.clicked.connect(self.go_back_to_orders_window)
        back_header_btn.setObjectName("back_header_button")
        header_widget_hbox.addWidget(back_header_btn)
        header_widget_hbox.addStretch()

        # ЛОГОТИП по центру
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Загружаем логотип
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_file_dir)
        logo_path = os.path.join(project_root, "ICONS", "logo.png")
        
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            # Масштабируем логотип до нужного размера
            logo_pixmap = logo_pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            # Если файл не найден, показываем текстовый логотип
            logo_label.setText("ОБУВЬ")
            logo_label.setStyleSheet("font-size: 28px; font-weight: bold; color: black;")
        
        header_widget_hbox.addWidget(logo_label)

        # Растягивающий элемент
        header_widget_hbox.addStretch()

        # ФИО пользователя
        user_data = self.database.take_user_data()
        fio_widget = QWidget()
        fio_layout = QVBoxLayout(fio_widget)
        fio_layout.addWidget(QLabel(user_data["user_name"].replace(" ", "\n"), objectName="FIO"))
        header_widget_hbox.addWidget(fio_widget)

        self.frame_layout.addWidget(header_widget)

        # Заголовок
        title = QLabel("Создание нового заказа")
        title.setObjectName("Title")
        self.frame_layout.addWidget(title)

        # Область с формой
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_container = QWidget()
        self.form_layout = QVBoxLayout(form_container)
        
        self.create_order_form()
        scroll_area.setWidget(form_container)
        self.frame_layout.addWidget(scroll_area)

        # Кнопка сохранения
        save_btn = QPushButton("Создать заказ")
        save_btn.setObjectName("button")
        save_btn.clicked.connect(self.create_order)
        self.frame_layout.addWidget(save_btn)

    def create_order_form(self):
        """Создает форму для ввода данных заказа"""
        # Выбор клиента
        self.client_combo = self.create_combo_field("Клиент:", self.get_clients_list())
        self.form_layout.addWidget(self.client_combo)

        # ПВЗ
        self.pvz_combo = self.create_combo_field("Пункт выдачи:", self.database.take_all_pvz_addresses())
        self.form_layout.addWidget(self.pvz_combo)

        # Статус заказа
        self.status_combo = self.create_combo_field("Статус:", ["Новый", "В обработке", "Завершен"])
        self.form_layout.addWidget(self.status_combo)

        # Код для получения
        self.code_input = self.create_input_field("Код для получения:", "Введите код")
        self.form_layout.addWidget(self.code_input)

        # Дата доставки
        self.delivery_date_input = self.create_input_field("Дата доставки (ДД.ММ.ГГГГ):", datetime.now().strftime("%d.%m.%Y"))
        self.form_layout.addWidget(self.delivery_date_input)

        # Блок добавления товаров
        self.create_products_section()
        
        # Таблица товаров в заказе
        self.create_order_items_table()

    def create_combo_field(self, label_text, items_list):
        """Создает поле с выпадающим списком"""
        widget = QWidget()
        widget.setFixedHeight(80)
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))
        combo = QComboBox()
        combo.addItems(items_list)
        combo.setObjectName("UpdateTextEdit")
        layout.addWidget(combo)
        
        return widget

    def create_input_field(self, label_text, placeholder):
        """Создает поле для ввода текста"""
        widget = QWidget()
        widget.setFixedHeight(80)
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setObjectName("UpdateTextEdit")
        layout.addWidget(input_field)
        
        return widget

    def create_products_section(self):
        """Создает секцию для добавления товаров в заказ"""
        products_widget = QWidget()
        products_layout = QVBoxLayout(products_widget)
        
        products_layout.addWidget(QLabel("Добавление товаров:", objectName="UpdateTextHint"))

        # Выбор товара и количества
        products_row = QWidget()
        products_row_layout = QHBoxLayout(products_row)

        # Выпадающий список товаров
        self.product_combo = QComboBox()
        self.load_available_products()
        self.product_combo.setObjectName("UpdateTextEdit")
        products_row_layout.addWidget(QLabel("Товар:"))
        products_row_layout.addWidget(self.product_combo)

        # Поле количества
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Количество")
        self.quantity_input.setText("1")
        self.quantity_input.setObjectName("UpdateTextEdit")
        self.quantity_input.setFixedWidth(100)
        products_row_layout.addWidget(QLabel("Количество:"))
        products_row_layout.addWidget(self.quantity_input)

        # Кнопка добавления
        add_product_btn = QPushButton("Добавить")
        add_product_btn.setObjectName("button")
        add_product_btn.clicked.connect(self.add_product_to_order)
        products_row_layout.addWidget(add_product_btn)

        products_layout.addWidget(products_row)
        self.form_layout.addWidget(products_widget)

    def create_order_items_table(self):
        """Создает таблицу товаров в заказе"""
        self.form_layout.addWidget(QLabel("Товары в заказе:", objectName="UpdateTextHint"))

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Артикул", "Наименование", "Количество", "Доступно", "Действия"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.setMaximumHeight(300)
        
        self.form_layout.addWidget(self.items_table)

    def load_available_products(self):
        """Загружает список доступных товаров"""
        try:
            products = self.database.get_all_items()
            self.available_products = products
            self.product_combo.clear()
            
            for product in products:
                display_text = f"{product['article']} - {product['name']} (остаток: {product['count']})"
                self.product_combo.addItem(display_text, product['article'])
                
        except Exception as e:
            print(f"Ошибка загрузки товаров: {e}")
            Messages.send_C_message("Ошибка загрузки списка товаров!")

    def get_clients_list(self):
        """Получает список клиентов"""
        try:
            # В реальной системе здесь был бы запрос к БД для получения клиентов
            # Пока используем фиктивные данные из user_import.xlsx
            clients = [
                "Михайлюк Анна Вячеславовна",
                "Ситдикова Елена Анатольевна", 
                "Ворсин Петр Евгеньевич",
                "Старикова Елена Павловна"
            ]
            return clients
        except Exception as e:
            print(f"Ошибка загрузки клиентов: {e}")
            return ["Клиент не выбран"]

    def add_product_to_order(self):
        """Добавляет товар в заказ"""
        try:
            # Получаем выбранный товар
            current_index = self.product_combo.currentIndex()
            if current_index < 0:
                Messages.send_C_message("Выберите товар!", "Ошибка")
                return

            product_article = self.product_combo.itemData(current_index)
            product = next((p for p in self.available_products if p['article'] == product_article), None)
            
            if not product:
                Messages.send_C_message("Товар не найден!")
                return

            # Проверяем количество
            try:
                quantity = int(self.quantity_input.text())
                if quantity <= 0:
                    Messages.send_C_message("Количество должно быть положительным числом!")
                    return
                    
                if quantity > product['count']:
                    Messages.send_C_message(f"Недостаточно товара на складе! Доступно: {product['count']}")
                    return
                    
            except ValueError:
                Messages.send_C_message("Введите корректное количество!")
                return

            # Проверяем, не добавлен ли уже товар
            existing_item = next((item for item in self.order_items if item['article'] == product_article), None)
            if existing_item:
                Messages.send_C_message("Этот товар уже добавлен в заказ!")
                return

            # Добавляем товар в заказ
            self.order_items.append({
                'article': product_article,
                'name': product['name'],
                'quantity': quantity,
                'available': product['count']
            })

            # Обновляем таблицу
            self.update_order_items_table()
            
            # Сбрасываем поля
            self.quantity_input.setText("1")
            
            Messages.send_I_message("Товар добавлен в заказ!")

        except Exception as e:
            Messages.send_C_message(f"Ошибка добавления товара: {str(e)}")

    def update_order_items_table(self):
        """Обновляет таблицу товаров в заказе"""
        self.items_table.setRowCount(len(self.order_items))
        
        for row, item in enumerate(self.order_items):
            # Артикул
            self.items_table.setItem(row, 0, QTableWidgetItem(item['article']))
            # Наименование
            self.items_table.setItem(row, 1, QTableWidgetItem(item['name']))
            # Количество
            quantity_item = QTableWidgetItem(str(item['quantity']))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_table.setItem(row, 2, quantity_item)
            # Доступно
            available_item = QTableWidgetItem(str(item['available']))
            available_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_table.setItem(row, 3, available_item)
            
            # Кнопка удаления
            delete_btn = QPushButton("Удалить")
            delete_btn.setObjectName("button")
            delete_btn.clicked.connect(lambda checked, r=row: self.remove_product_from_order(r))
            self.items_table.setCellWidget(row, 4, delete_btn)

    def remove_product_from_order(self, row_index):
        """Удаляет товар из заказа"""
        if 0 <= row_index < len(self.order_items):
            removed_item = self.order_items.pop(row_index)
            self.update_order_items_table()
            Messages.send_I_message(f"Товар '{removed_item['name']}' удален из заказа")

    def create_order(self):
        """Создает новый заказ"""
        try:
            # Валидация данных
            if not self.validate_order_data():
                return

            # Подготавливаем данные заказа
            order_data = {
                'client_name': self.client_combo.layout().itemAt(1).widget().currentText(),
                'pvz_id': int(self.pvz_combo.layout().itemAt(1).widget().currentText().split(' | ')[0]),
                'status': self.status_combo.layout().itemAt(1).widget().currentText(),
                'code': int(self.code_input.layout().itemAt(1).widget().text()),
                'delivery_date': self.parse_date(self.delivery_date_input.layout().itemAt(1).widget().text()),
                'items': self.order_items
            }

            # Создаем заказ в БД
            if self.database.create_new_order(order_data):
                Messages.send_I_message("Заказ успешно создан!")
                
                # Обновляем список заказов в кэшированном окне
                self.refresh_orders_frame()
                
                self.go_back_to_orders_window()
            else:
                Messages.send_C_message("Ошибка создания заказа в базе данных!")

        except Exception as e:
            Messages.send_C_message(f"Ошибка создания заказа: {str(e)}")

    def refresh_orders_frame(self):
        """Обновляет данные в окне списка заказов"""
        try:
            # Получаем существующий фрейм заказов из кэша
            orders_frame = self.controller.frames_cache.get('OrdersCardsFrame')
            if orders_frame:
                # Вызываем существующий метод обновления
                orders_frame.update_orders_display()
        except Exception as e:
            print(f"Ошибка обновления списка заказов: {e}")

    def validate_order_data(self):
        """Валидация данных заказа"""
        # Проверяем клиента
        client = self.client_combo.layout().itemAt(1).widget().currentText()
        if not client or client == "Клиент не выбран":
            Messages.send_C_message("Выберите клиента!")
            return False

        # Проверяем ПВЗ
        pvz_text = self.pvz_combo.layout().itemAt(1).widget().currentText()
        if not pvz_text:
            Messages.send_C_message("Выберите пункт выдачи!")
            return False

        # Проверяем код
        try:
            code = int(self.code_input.layout().itemAt(1).widget().text())
            if code <= 0:
                Messages.send_C_message("Код должен быть положительным числом!")
                return False
        except ValueError:
            Messages.send_C_message("Введите корректный код (число)!")
            return False

        # Проверяем дату доставки
        delivery_date_text = self.delivery_date_input.layout().itemAt(1).widget().text()
        if not delivery_date_text:
            Messages.send_C_message("Введите дату доставки!")
            return False
        
        try:
            delivery_date = self.parse_date(delivery_date_text)
            if delivery_date < datetime.now().date():
                Messages.send_C_message("Дата доставки не может быть в прошлом!")
                return False
        except ValueError:
            Messages.send_C_message("Введите корректную дату доставки (ДД.ММ.ГГГГ)!")
            return False

        # Проверяем товары в заказе
        if not self.order_items:
            Messages.send_C_message("Добавьте хотя бы один товар в заказ!")
            return False

        # Проверяем, что все товары все еще доступны в нужном количестве
        for item in self.order_items:
            product = next((p for p in self.available_products if p['article'] == item['article']), None)
            if not product:
                Messages.send_C_message(f"Товар {item['article']} больше не доступен!")
                return False
            if item['quantity'] > product['count']:
                Messages.send_C_message(f"Недостаточно товара '{item['name']}' на складе! Доступно: {product['count']}")
                return False

        return True

    def parse_date(self, date_str):
        """Парсит дату из строки"""
        try:
            if '.' in date_str:
                return datetime.strptime(date_str, "%d.%m.%Y").date()
            elif '-' in date_str:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                raise ValueError("Неверный формат даты")
        except Exception as e:
            raise ValueError(f"Неверный формат даты: {date_str}")

    def go_back_to_orders_window(self):
        """Возврат к списку заказов с обновлением данных"""
        # Удаляем старый фрейм из кэша
        if 'OrdersCardsFrame' in self.controller.frames_cache:
            old_frame = self.controller.frames_cache.pop('OrdersCardsFrame')
            self.controller.frame_container.removeWidget(old_frame)
            old_frame.deleteLater()
        
        # Создаем новый фрейм
        from FRAMES import OrdersCardsWindow
        self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)