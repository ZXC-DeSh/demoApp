from PySide6.QtWidgets import (QFrame, QPushButton, QHBoxLayout, QScrollArea,
                               QWidget, QVBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
import Messages
from FRAMES import HomePageWindow, OrdersCardsWindow
from StaticStorage import Storage
from PySide6.QtGui import QPixmap
import os

class OrderDetailsFrame(QFrame):
    def __init__(self, controller):
        """
        Конструктор класса детального просмотра заказа
        :param controller: "self" из класса MainApplicationClass
        """
        super().__init__()
        self.controller = controller
        self.database = controller.db
        
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
        title = QLabel("Детали заказа")
        title.setObjectName("Title")
        self.frame_layout.addWidget(title)

        # Область с информацией
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        info_container = QWidget()
        self.info_layout = QVBoxLayout(info_container)
        
        self.load_order_details()
        scroll_area.setWidget(info_container)
        self.frame_layout.addWidget(scroll_area)

    def load_order_details(self):
        """Загружает и отображает детальную информацию о заказе"""
        try:
            order_id = Storage.get_order_id()
            if not order_id:
                Messages.send_C_message("Не выбран заказ для просмотра!")
                self.go_back_to_orders_window()
                return

            # Получаем данные заказа
            order_data = self.database.take_single_order_data()
            if not order_data:
                Messages.send_C_message("Заказ не найден!")
                self.go_back_to_orders_window()
                return

            # Отображаем основную информацию о заказе
            self.display_order_info(order_data)
            
            # Отображаем состав заказа
            self.display_order_items(order_id)
            
            # Отображаем итоговую информацию
            self.display_order_summary(order_id)

        except Exception as e:
            Messages.send_C_message(f"Ошибка загрузки деталей заказа: {str(e)}")

    def display_order_info(self, order_data):
        """Отображает основную информацию о заказе"""
        # Блок с основной информацией
        info_widget = QWidget()
        info_widget.setObjectName("item_card")
        info_layout = QVBoxLayout(info_widget)

        # Заголовок с номером заказа и статусом
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"Заказ #{order_data['id']}", 
                                     objectName="cardText",
                                     styleSheet="font-weight: bold; font-size: 20px;"))
        header_layout.addStretch()
        
        # Статус с цветовым оформлением
        status_label = QLabel(order_data['status'])
        status_style = self.get_status_style(order_data['status'])
        status_label.setStyleSheet(status_style)
        status_label.setObjectName("cardText")
        header_layout.addWidget(status_label)
        
        info_layout.addLayout(header_layout)

        # Информация о клиенте
        info_layout.addWidget(QLabel(f"👤 Клиент: {order_data['client_name']}", 
                                   objectName="cardText"))

        # Адрес пункта выдачи
        pvz_address = self.database.take_pvz_address(order_data['pvz'])
        info_layout.addWidget(QLabel(f"📍 Пункт выдачи: {pvz_address}", 
                                   objectName="cardText", 
                                   wordWrap=True))

        # Даты
        dates_layout = QHBoxLayout()
        dates_layout.addWidget(QLabel(f"📅 Дата создания: {order_data['create_date']}", 
                                    objectName="cardText"))
        dates_layout.addWidget(QLabel(f"🚚 Дата доставки: {order_data['delivery_date']}", 
                                    objectName="cardText"))
        info_layout.addLayout(dates_layout)

        # Код получения
        info_layout.addWidget(QLabel(f"🔑 Код получения: {order_data['code']}", 
                                   objectName="cardText"))

        self.info_layout.addWidget(info_widget)

    def display_order_items(self, order_id):
        """Отображает таблицу с составом заказа"""
        # Заголовок раздела
        items_title = QLabel("Состав заказа:")
        items_title.setObjectName("UpdateTextHint")
        items_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        self.info_layout.addWidget(items_title)

        # Получаем товары заказа
        order_items = self.database.get_order_items_with_prices(order_id)
        if not order_items:
            self.info_layout.addWidget(QLabel("Товары в заказе отсутствуют", 
                                            objectName="cardText"))
            return

        # Создаем таблицу
        items_table = QTableWidget()
        items_table.setColumnCount(5)
        items_table.setHorizontalHeaderLabels(["Артикул", "Наименование", "Цена", "Кол-во", "Сумма"])
        items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        items_table.setRowCount(len(order_items))

        total_amount = 0

        for row, item in enumerate(order_items):
            # Артикул
            items_table.setItem(row, 0, QTableWidgetItem(item['article']))
            
            # Наименование
            items_table.setItem(row, 1, QTableWidgetItem(item['name']))
            
            # Цена
            price_item = QTableWidgetItem(f"{item['cost']:.2f} ₽")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(row, 2, price_item)
            
            # Количество
            quantity_item = QTableWidgetItem(str(item['quantity']))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(row, 3, quantity_item)
            
            # Сумма
            item_total = item['cost'] * item['quantity']
            total_item = QTableWidgetItem(f"{item_total:.2f} ₽")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            items_table.setItem(row, 4, total_item)
            
            total_amount += item_total

        items_table.setMaximumHeight(300)
        self.info_layout.addWidget(items_table)

        # Итоговая сумма
        total_widget = QWidget()
        total_layout = QHBoxLayout(total_widget)
        total_layout.addStretch()
        total_label = QLabel(f"Итого: {total_amount:.2f} ₽")
        total_label.setObjectName("cardText")
        total_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #2E8B57;")
        total_layout.addWidget(total_label)
        self.info_layout.addWidget(total_widget)

    def display_order_summary(self, order_id):
        """Отображает сводную информацию о заказе"""
        summary_widget = QWidget()
        summary_widget.setObjectName("item_card")
        summary_layout = QVBoxLayout(summary_widget)

        # Заголовок
        summary_layout.addWidget(QLabel("Сводная информация:", 
                                      objectName="UpdateTextHint",
                                      styleSheet="font-weight: bold;"))

        # Получаем дополнительные данные
        order_items = self.database.get_order_items_with_prices(order_id)
        total_products = len(order_items)
        total_quantity = sum(item['quantity'] for item in order_items)
        total_amount = sum(item['cost'] * item['quantity'] for item in order_items)

        # Статистика
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(QLabel(f"• Количество позиций: {total_products}", 
                                    objectName="cardText"))
        stats_layout.addWidget(QLabel(f"• Общее количество товаров: {total_quantity}", 
                                    objectName="cardText"))
        stats_layout.addWidget(QLabel(f"• Общая стоимость: {total_amount:.2f} ₽", 
                                    objectName="cardText"))
        
        summary_layout.addLayout(stats_layout)
        self.info_layout.addWidget(summary_widget)

    def get_status_style(self, status):
        """Возвращает стиль для статуса заказа"""
        status_styles = {
            "Новый": "background-color: #2E8B57; color: white; padding: 5px 10px; border-radius: 10px;",
            "Завершен": "background-color: #4682B4; color: white; padding: 5px 10px; border-radius: 10px;",
            "В обработке": "background-color: #FFA500; color: black; padding: 5px 10px; border-radius: 10px;",
        }
        return status_styles.get(status, "background-color: #696969; color: white; padding: 5px 10px; border-radius: 10px;")

    def go_back_to_orders_window(self):
        """Возврат к списку заказов"""
        self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)