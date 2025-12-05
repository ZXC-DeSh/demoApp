from PySide6.QtWidgets import (QFrame, QPushButton, QHBoxLayout, QScrollArea, QComboBox,
                               QFileDialog, QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from datetime import datetime
import Messages
from FRAMES import HomePageWindow, OrdersCardsWindow
from StaticStorage import Storage
from PySide6.QtGui import QPixmap
import os

class UpdateOrderFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db
        
        # Данные заказа
        self.order_data = {}  # Инициализируем пустым словарем
        self.order_items = []
        
        self.frame_layout = QVBoxLayout(self)
        
        # Сначала загружаем данные, потом создаем UI
        self.load_order_data()
        self.setup_ui()

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

        user_data = self.database.take_user_data()
        fio_widget = QWidget()
        fio_layout = QVBoxLayout(fio_widget)
        fio_layout.addWidget(QLabel(user_data["user_name"].replace(" ", "\n"), objectName="FIO"))
        header_widget_hbox.addWidget(fio_widget)

        self.frame_layout.addWidget(header_widget)
        
        title = QLabel("Просмотр заказа" if Storage.get_user_role() != "Администратор" else "Редактирование заказа")
        title.setObjectName("Title")
        self.frame_layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_container = QWidget()
        self.form_layout = QVBoxLayout(form_container)
        self.form_layout.setSpacing(0)  # УБИРАЕМ ВСЕ ОТСТУПЫ МЕЖДУ ЭЛЕМЕНТАМИ
                
        self.create_order_form()
        scroll_area.setWidget(form_container)
        self.frame_layout.addWidget(scroll_area)

        # Только администратор может сохранять изменения и удалять
        if Storage.get_user_role() == "Администратор":
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
            
            # Загружаем товары заказа (только для информации)
            self.order_items = self.database.get_order_items_with_prices(self.order_data['id'])
            
        except Exception as e:
            Messages.send_C_message(f"Ошибка загрузки данных заказа: {str(e)}", "Ошибка загрузки")
            import traceback
            traceback.print_exc()

    def create_order_form(self):
        """Создает форму редактирования/просмотра заказа"""
        if not self.order_data:
            Messages.send_C_message("Данные заказа не загружены!")
            return

        # Проверяем роль пользователя
        is_admin = Storage.get_user_role() == "Администратор"
        
        # 1. Артикул заказа (номер заказа или артикул товара)
        order_items = self.database.get_order_items(self.order_data['id'])
        article = ""
        if order_items:
            article = order_items[0]['article'] if order_items[0]['article'] else f"ORD{self.order_data['id']}"
        else:
            article = f"ORD{self.order_data['id']}"
            
        self.article_input = self.create_input_field("Артикул заказа:", article, not is_admin)
        self.form_layout.addWidget(self.article_input)

        # 2. Статус заказа
        self.status_combo = self.create_combo_field("Статус заказа:", ["Новый", "В обработке", "Завершен"], not is_admin)
        self.set_combo_to_value(self.status_combo, self.order_data.get('status', 'Новый'))
        self.form_layout.addWidget(self.status_combo)

        # 3. Адрес пункта выдачи
        self.pvz_combo = self.create_combo_field("Адрес пункта выдачи:", self.database.take_all_pvz_addresses(), not is_admin)
        self.set_combo_to_value(self.pvz_combo, f"{self.order_data.get('pvz', '')} | {self.database.take_pvz_address(self.order_data.get('pvz', ''))}")
        self.form_layout.addWidget(self.pvz_combo)

        # 4. Дата заказа
        self.create_date_input = self.create_input_field("Дата заказа:", str(self.order_data.get('create_date', '')), True)
        self.form_layout.addWidget(self.create_date_input)
        
        # 5. Дата выдачи (доставки)
        self.delivery_date_input = self.create_input_field("Дата выдачи:", str(self.order_data.get('delivery_date', '')), not is_admin)
        self.form_layout.addWidget(self.delivery_date_input)

        # Информация о составе заказа
        order_items_widget = QWidget()
        order_items_layout = QVBoxLayout(order_items_widget)
        order_items_layout.setSpacing(3)  # Минимальный отступ
        order_items_layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок "Состав заказа" в том же стиле что и другие подсказки
        items_title_label = QLabel("Состав заказа:")
        items_title_label.setObjectName("UpdateTextHint")
        items_title_label.setContentsMargins(0, 5, 0, 3)  # Небольшие отступы сверху и снизу
        order_items_layout.addWidget(items_title_label)
        
        # Товары в заказе
        items_container = QWidget()
        items_container_layout = QVBoxLayout(items_container)
        items_container_layout.setSpacing(2)  # Минимальный отступ между товарами
        items_container_layout.setContentsMargins(0, 0, 0, 0)
                
        if self.order_items:
            for item in self.order_items:
                item_label = QLabel(f"  • {item['name']} (Артикул: {item['article']}, Количество: {item['quantity']})")
                item_label.setObjectName("cardText")
                item_label.setStyleSheet("font-size: 18px; color: black; padding: 0px;")
                items_container_layout.addWidget(item_label)
        else:
            no_items_label = QLabel("  • Товары отсутствуют")
            no_items_label.setObjectName("cardText")
            no_items_label.setStyleSheet("font-size: 18px; color: black; padding: 0px;")
            items_container_layout.addWidget(no_items_label)
        
        order_items_layout.addWidget(items_container)
        self.form_layout.addWidget(order_items_widget)

    def create_combo_field(self, label_text, items_list, readonly=False):
        widget = QWidget()
        widget.setMaximumHeight(70)  # Ограничиваем максимальную высоту
        widget.setMinimumHeight(60)  # Минимальная высота
        layout = QVBoxLayout(widget)
        layout.setSpacing(1)  # ОЧЕНЬ маленький отступ между меткой и полем
        layout.setContentsMargins(0, 0, 0, 0)  # Нет внешних отступов
        label = QLabel(label_text, objectName="UpdateTextHint")
        label.setContentsMargins(0, 0, 0, 1)  # Минимальный отступ снизу
        layout.addWidget(label)
        combo = QComboBox()
        combo.addItems(items_list)
        combo.setEnabled(not readonly)
        combo.setObjectName("UpdateTextEdit")
        layout.addWidget(combo)
        return widget

    def create_input_field(self, label_text, value, readonly=False):
        widget = QWidget()
        widget.setMaximumHeight(70)  # Ограничиваем максимальную высоту
        widget.setMinimumHeight(60)  # Минимальная высота
        layout = QVBoxLayout(widget)
        layout.setSpacing(1)  # ОЧЕНЬ маленький отступ между меткой и полем
        layout.setContentsMargins(0, 0, 0, 0)  # Нет внешних отступов
        label = QLabel(label_text, objectName="UpdateTextHint")
        label.setContentsMargins(0, 0, 0, 1)  # Минимальный отступ снизу
        layout.addWidget(label)
        input_field = QLineEdit()
        input_field.setText(str(value))
        input_field.setReadOnly(readonly)
        input_field.setObjectName("UpdateTextEdit")
        layout.addWidget(input_field)
        return widget

    def set_combo_to_value(self, combo_widget, value):
        combo = combo_widget.layout().itemAt(1).widget()
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def save_changes(self):
        """Сохраняет изменения заказа (только для администратора)"""
        if Storage.get_user_role() != "Администратор":
            Messages.send_C_message("У вас нет прав для редактирования заказов!", "Ошибка доступа")
            return
            
        try:
            if not self.validate_order_data():
                return

            # Подготавливаем данные
            order_data = {
                'id': self.order_data['id'],
                'pvz_id': int(self.pvz_combo.layout().itemAt(1).widget().currentText().split(' | ')[0]),
                'status': self.status_combo.layout().itemAt(1).widget().currentText(),
                'delivery_date': self.parse_date(self.delivery_date_input.layout().itemAt(1).widget().text()),
            }

            if self.database.update_order_data(order_data):
                Messages.send_I_message("Заказ успешно обновлен!")
                # Обновляем список заказов
                self.refresh_orders_window()
                self.go_back_to_orders_window()
            else:
                Messages.send_C_message("Ошибка обновления заказа!")

        except Exception as e:
            Messages.send_C_message(f"Ошибка сохранения: {str(e)}")
            import traceback
            traceback.print_exc()

    def refresh_orders_window(self):
        """Обновляет данные в окне списка заказов"""
        try:
            # Получаем существующий фрейм заказов из кэша
            orders_frame = self.controller.frames_cache.get('OrdersCardsFrame')
            if orders_frame:
                # Вызываем существующий метод обновления
                orders_frame.update_orders_display()
                print("Список заказов обновлен после сохранения")
        except Exception as e:
            print(f"Ошибка обновления списка заказов: {e}")

    def validate_order_data(self):
        """Валидация данных заказа (только для администратора)"""
        # Проверка даты выдачи
        delivery_date = self.delivery_date_input.layout().itemAt(1).widget().text()
        if not delivery_date:
            Messages.send_C_message("Введите дату выдачи!", "Ошибка")
            return False

        try:
            # Пробуем распарсить дату
            self.parse_date(delivery_date)
        except Exception:
            Messages.send_C_message("Введите корректную дату выдачи!", "Ошибка")
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
            raise ValueError("Неверный формат даты")

    def delete_order(self):
        """Удаляет заказ (только для администратора)"""
        if Storage.get_user_role() != "Администратор":
            Messages.send_C_message("У вас нет прав для удаления заказов!", "Ошибка доступа")
            return
            
        if Messages.send_I_message("Вы точно хотите удалить этот заказ?", "Подтверждение удаления") < 20000:
            if self.database.delete_order(self.order_data['id']):
                Messages.send_I_message("Заказ успешно удален!")
                # Обновляем список заказов
                self.refresh_orders_window()
                self.go_back_to_orders_window()
            else:
                Messages.send_C_message("Ошибка удаления заказа!")

    def go_back_to_orders_window(self):
        """Возврат к списку заказов"""
        self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)