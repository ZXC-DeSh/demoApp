from PySide6.QtWidgets import (QFrame, QPushButton, QHBoxLayout, QScrollArea, QComboBox,
                               QFileDialog, QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from datetime import datetime
import Messages
from FRAMES import HomePageWindow, OrdersCardsWindow
from StaticStorage import Storage


class UpdateOrderFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db
        
        # Данные заказа
        self.order_items = []
        self.available_products = []
        
        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()
        self.load_order_data()

    def setup_ui(self):
        """Генерация интерфейса"""
        # Шапка
        header_widget = QWidget()
        header_widget.setObjectName("header_widget")
        header_widget_hbox = QHBoxLayout(header_widget)

        back_header_btn = QPushButton("< Назад")
        back_header_btn.setFixedWidth(150)
        back_header_btn.clicked.connect(self.go_back_to_orders_window)
        back_header_btn.setObjectName("back_header_button")
        header_widget_hbox.addWidget(back_header_btn)
        header_widget_hbox.addStretch()

        user_data = self.database.take_user_data()
        fio_widget = QWidget()
        fio_layout = QVBoxLayout(fio_widget)
        fio_layout.addWidget(QLabel(user_data["user_name"].replace(" ", "\n"), objectName="FIO"))
        header_widget_hbox.addWidget(fio_widget)

        self.frame_layout.addWidget(header_widget)
        
        title = QLabel("Редактирование заказа")
        title.setObjectName("Title")
        self.frame_layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_container = QWidget()
        self.form_layout = QVBoxLayout(form_container)
        
        self.create_order_form()
        scroll_area.setWidget(form_container)
        self.frame_layout.addWidget(scroll_area)

        save_btn = QPushButton("Сохранить изменения")
        save_btn.setObjectName("button")
        save_btn.clicked.connect(self.save_changes)
        self.frame_layout.addWidget(save_btn)

        delete_btn = QPushButton("Удалить заказ")
        delete_btn.setObjectName("button")
        delete_btn.clicked.connect(self.delete_order)
        self.frame_layout.addWidget(delete_btn)

    def load_order_data(self):
        """Загружает данные заказа для редактирования"""
        try:
            self.order_data = self.database.take_single_order_data()
            if not self.order_data:
                Messages.send_C_message("Заказ не найден!")
                self.go_back_to_orders_window()
                return
            
            # Загружаем товары заказа
            self.order_items = self.database.get_order_items_with_prices(self.order_data['id'])
            
        except Exception as e:
            Messages.send_C_message(f"Ошибка загрузки данных заказа: {str(e)}")

    def create_order_form(self):
        """Создает форму редактирования заказа"""
        # Клиент
        self.client_input = self.create_input_field("Клиент:", self.order_data.get('client_name', ''), True)
        self.form_layout.addWidget(self.client_input)

        # ПВЗ
        self.pvz_combo = self.create_combo_field("Пункт выдачи:", self.database.take_all_pvz_addresses())
        self.set_combo_to_value(self.pvz_combo, f"{self.order_data.get('pvz', '')} | {self.database.take_pvz_address(self.order_data.get('pvz', ''))}")
        self.form_layout.addWidget(self.pvz_combo)

        # Статус
        self.status_combo = self.create_combo_field("Статус:", ["Новый", "В обработке", "Завершен"])
        self.set_combo_to_value(self.status_combo, self.order_data.get('status', 'Новый'))
        self.form_layout.addWidget(self.status_combo)

        # Код
        self.code_input = self.create_input_field("Код для получения:", str(self.order_data.get('code', '')), False)
        self.form_layout.addWidget(self.code_input)

        # Даты
        self.create_date_input = self.create_input_field("Дата создания:", str(self.order_data.get('create_date', '')), True)
        self.form_layout.addWidget(self.create_date_input)
        
        self.delivery_date_input = self.create_input_field("Дата доставки:", str(self.order_data.get('delivery_date', '')), False)
        self.form_layout.addWidget(self.delivery_date_input)

        # Таблица товаров
        self.create_order_items_table()

    def create_combo_field(self, label_text, items_list):
        widget = QWidget()
        widget.setFixedHeight(80)
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))
        combo = QComboBox()
        combo.addItems(items_list)
        combo.setObjectName("UpdateTextEdit")
        layout.addWidget(combo)
        return widget

    def create_input_field(self, label_text, value, readonly=False):
        widget = QWidget()
        widget.setFixedHeight(80)
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))
        input_field = QLineEdit()
        input_field.setText(value)
        input_field.setReadOnly(readonly)
        input_field.setObjectName("UpdateTextEdit")
        layout.addWidget(input_field)
        return widget

    def set_combo_to_value(self, combo_widget, value):
        combo = combo_widget.layout().itemAt(1).widget()
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def create_order_items_table(self):
        """Создает таблицу товаров заказа"""
        self.form_layout.addWidget(QLabel("Товары в заказе:", objectName="UpdateTextHint"))

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Артикул", "Наименование", "Количество", "Действия"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.setMaximumHeight(300)
        
        self.update_order_items_table()
        self.form_layout.addWidget(self.items_table)

    def update_order_items_table(self):
        """Обновляет таблицу товаров"""
        self.items_table.setRowCount(len(self.order_items))
        
        for row, item in enumerate(self.order_items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item['article']))
            self.items_table.setItem(row, 1, QTableWidgetItem(item['name']))
            
            quantity_item = QTableWidgetItem(str(item['quantity']))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_table.setItem(row, 2, quantity_item)
            
            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(lambda checked, r=row: self.remove_order_item(r))
            self.items_table.setCellWidget(row, 3, delete_btn)

    def remove_order_item(self, row_index):
        """Удаляет товар из заказа"""
        if 0 <= row_index < len(self.order_items):
            self.order_items.pop(row_index)
            self.update_order_items_table()
            Messages.send_I_message("Товар удален из заказа")

    def save_changes(self):
        """Сохраняет изменения заказа"""
        try:
            if not self.validate_order_data():
                return

            # Подготавливаем данные
            order_data = {
                'id': self.order_data['id'],
                'pvz_id': int(self.pvz_combo.layout().itemAt(1).widget().currentText().split(' | ')[0]),
                'status': self.status_combo.layout().itemAt(1).widget().currentText(),
                'code': int(self.code_input.layout().itemAt(1).widget().text()),
                'delivery_date': self.parse_date(self.delivery_date_input.layout().itemAt(1).widget().text()),
                'items': self.order_items
            }

            if self.database.update_order_data(order_data):
                Messages.send_I_message("Заказ успешно обновлен!")
                self.go_back_to_orders_window()
            else:
                Messages.send_C_message("Ошибка обновления заказа!")

        except Exception as e:
            Messages.send_C_message(f"Ошибка сохранения: {str(e)}")

    def validate_order_data(self):
        """Валидация данных заказа"""
        # Проверка кода
        try:
            code = int(self.code_input.layout().itemAt(1).widget().text())
            if code <= 0:
                Messages.send_C_message("Код должен быть положительным числом!")
                return False
        except ValueError:
            Messages.send_C_message("Введите корректный код!")
            return False

        # Проверка даты доставки
        delivery_date = self.delivery_date_input.layout().itemAt(1).widget().text()
        if not delivery_date:
            Messages.send_C_message("Введите дату доставки!")
            return False

        # Проверка товаров
        if not self.order_items:
            Messages.send_C_message("Заказ должен содержать хотя бы один товар!")
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
                return datetime.now().date()
        except Exception:
            return datetime.now().date()

    def delete_order(self):
        """Удаляет заказ"""
        if Messages.send_I_message("Вы точно хотите удалить этот заказ?") < 20000:
            if self.database.delete_order(self.order_data['id']):
                Messages.send_I_message("Заказ успешно удален!")
                self.go_back_to_orders_window()
            else:
                Messages.send_C_message("Ошибка удаления заказа!")

    def go_back_to_orders_window(self):
        """Возврат к списку заказов"""
        self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)