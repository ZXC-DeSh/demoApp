from PySide6.QtWidgets import (QFrame, QPushButton, QHBoxLayout, QLineEdit, QCheckBox,
                               QComboBox, QWidget, QVBoxLayout, QLabel, QScrollArea)
from PySide6.QtCore import Qt
import Messages
from FRAMES import HomePageWindow, UpdateOrderWindow, CreateOrderWindow
from StaticStorage import Storage


class OrdersCardsFrame(QFrame):
    def __init__(self, controller):
        """
        Конструктор класса
        :param controller: "self" из класса MainApplicationClass (который главное окно)
        """
        super().__init__()
        self.controller = controller
        self.database = controller.db

        # Создание разметки окна
        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        """ Генерация интерфейса """
        # Шапка с кнопкой назад и ФИО
        header_widget = QWidget()
        header_widget.setObjectName("header_widget")
        header_widget_hbox = QHBoxLayout(header_widget)

        # Кнопка "Назад"
        back_header_btn = QPushButton("< Назад")
        back_header_btn.setFixedWidth(150)
        back_header_btn.clicked.connect(self.go_back_to_home_window)
        back_header_btn.setObjectName("back_header_button")
        header_widget_hbox.addWidget(back_header_btn)
        header_widget_hbox.addStretch()

        # ФИО пользователя
        user_data = self.database.take_user_data()
        fio_widget = QWidget()
        fio_layout = QVBoxLayout(fio_widget)
        fio_layout.addWidget(QLabel(user_data["user_name"].replace(" ", "\n"), objectName="FIO"))
        header_widget_hbox.addWidget(fio_widget)

        self.frame_layout.addWidget(header_widget)

        # Заголовок
        title = QLabel("Список заказов")
        title.setObjectName("Title")
        self.frame_layout.addWidget(title)

        # Область прокрутки для списка заказов
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.update_orders_display()
        self.frame_layout.addWidget(self.scroll_area)

        # Кнопка добавления заказа (только для администратора)
        if Storage.get_user_role() == "Администратор":
            create_order_btn = QPushButton("Добавить заказ")
            create_order_btn.setObjectName("button")
            create_order_btn.clicked.connect(self.go_to_create_order_window)
            self.frame_layout.addWidget(create_order_btn)

    def update_orders_display(self):
        """Обновляет отображение списка заказов"""
        orders_data = self.database.take_all_orders_rows()
        container = self.create_orders_cards_from_list(orders_data)
        self.scroll_area.setWidget(container)

    def create_orders_cards_from_list(self, orders_list):
        """Создаёт виджет с карточками заказов"""
        cards_container = QWidget()
        cards_container_layout = QVBoxLayout(cards_container)

        if not orders_list:
            # Если заказов нет
            no_orders_label = QLabel("Заказы отсутствуют")
            no_orders_label.setObjectName("cardText")
            no_orders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cards_container_layout.addWidget(no_orders_label)
            return cards_container

        for order in orders_list:
            order_card = self.create_single_order_card(order)
            cards_container_layout.addWidget(order_card)

        return cards_container

    def create_single_order_card(self, order):
        """Создает карточку для одного заказа"""
        order_card = QWidget()
        order_card.setObjectName("item_card")
        order_card.setFixedHeight(200)
        order_card_hbox = QHBoxLayout(order_card)

        # Основная информация о заказе
        info_widget = QWidget()
        info_widget.setObjectName("update_button")
        info_layout = QVBoxLayout(info_widget)

        # Номер заказа и статус
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"Заказ #{order['id']}", objectName="cardText", 
                                     styleSheet="font-weight: bold; font-size: 18px;"))
        header_layout.addStretch()
        header_layout.addWidget(QLabel(f"Статус: {order['status']}", objectName="cardText"))
        info_layout.addLayout(header_layout)

        # Информация о клиенте
        info_layout.addWidget(QLabel(f"Клиент: {order['client_name']}", objectName="cardText"))

        # Адрес пункта выдачи
        pvz_address = self.database.take_pvz_address(order['pvz'])
        info_layout.addWidget(QLabel(f"ПВЗ: {pvz_address}", objectName="cardText", wordWrap=True))

        # Даты
        dates_layout = QHBoxLayout()
        dates_layout.addWidget(QLabel(f"Создан: {order['create_date']}", objectName="cardText"))
        dates_layout.addWidget(QLabel(f"Доставка: {order['delivery_date']}", objectName="cardText"))
        info_layout.addLayout(dates_layout)

        # Код получения
        info_layout.addWidget(QLabel(f"Код получения: {order['code']}", objectName="cardText"))

        # Состав заказа
        order_items = self.database.get_order_items(order['id'])
        items_text = ", ".join([f"{item['name']} x{item['quantity']}" for item in order_items[:3]])  # Показываем первые 3 товара
        if len(order_items) > 3:
            items_text += f" ... (всего {len(order_items)} товаров)"
        
        info_layout.addWidget(QLabel(f"Товары: {items_text}", objectName="cardText", wordWrap=True))

        order_card_hbox.addWidget(info_widget)

        # Блок статуса (справа)
        status_block = self.create_order_status_block(order['status'])
        order_card_hbox.addWidget(status_block)

        # Блок кнопок (для всех пользователей - детали, для администратора - редактирование)
        buttons_widget = QWidget()
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setSpacing(10)

        # Кнопка "Детали" - для всех ролей
        details_btn = QPushButton("Детали")
        details_btn.setFixedSize(100, 40)
        details_btn.setObjectName("button")
        details_btn.setAccessibleName(str(order['id']))
        details_btn.clicked.connect(self.go_to_order_details_window)
        buttons_layout.addWidget(details_btn)

        # Кнопка "Редактировать" - только для администратора
        if Storage.get_user_role() == "Администратор":
            edit_btn = QPushButton("Редактировать")
            edit_btn.setFixedSize(100, 40)
            edit_btn.setObjectName("button")
            edit_btn.setAccessibleName(str(order['id']))
            edit_btn.clicked.connect(self.go_to_order_update_window)
            buttons_layout.addWidget(edit_btn)

        order_card_hbox.addWidget(buttons_widget)

        return order_card

    def create_order_status_block(self, order_status):
        """Создает блок со статусом заказа"""
        widget = QWidget()
        widget.setFixedSize(120, 120)
        widget.setObjectName("order_status_widget")
        
        # Динамические стили в зависимости от статуса
        status_styles = {
            "Новый": "background-color: #2E8B57; color: white;",  # Зеленый
            "Завершен": "background-color: #4682B4; color: white;",  # Синий
            "В обработке": "background-color: #FFA500; color: black;",  # Оранжевый
        }
        
        style = status_styles.get(order_status, "background-color: #696969; color: white;")  # Серый по умолчанию
        
        layout = QVBoxLayout(widget)
        status_label = QLabel(order_status)
        status_label.setObjectName("order_status")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(style)
        layout.addWidget(status_label)
        
        return widget

    def go_to_order_update_window(self):
        """Переход в окно редактирования заказа"""
        if Storage.get_user_role() == "Администратор":
            sender = self.sender()
            order_id = sender.accessibleName()
            print(f"Переход к редактированию заказа: {order_id}")
            Storage.set_order_id(order_id)
            self.controller.switch_window(UpdateOrderWindow.UpdateOrderFrame)

    def go_to_create_order_window(self):
        """Переход в окно создания заказа"""
        print("Переход в окно создания заказа")
        self.controller.switch_window(CreateOrderWindow.CreateOrderFrame)

    def go_to_order_details_window(self):
        """Переход к детальному просмотру заказа"""
        sender = self.sender()
        order_id = sender.accessibleName()
        Storage.set_order_id(order_id)
        from FRAMES import OrderDetailsWindow
        self.controller.switch_window(OrderDetailsWindow.OrderDetailsFrame)

    def go_back_to_home_window(self):
        if Messages.send_I_message("Вы точно хотите прекратить редактирование?") < 20000:
            # Очищаем временные данные
            Storage.set_item_id(None)
            Storage.set_order_id(None)
            self.controller.switch_window(HomePageWindow.HomeFrame)