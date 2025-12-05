from PySide6.QtWidgets import (QFrame, QPushButton, QHBoxLayout, QLineEdit, QCheckBox,
                               QComboBox, QWidget, QVBoxLayout, QLabel, QScrollArea)
from PySide6.QtCore import Qt
import Messages
from FRAMES import HomePageWindow, UpdateOrderWindow, CreateOrderWindow
from StaticStorage import Storage
from PySide6.QtGui import QPixmap
import os

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
        try:
            print("Начало обновления списка заказов...")
            orders_data = self.database.take_all_orders_rows()
            
            if not orders_data:
                print("Нет данных о заказах")
                # Создаем заглушку
                container = QWidget()
                layout = QVBoxLayout(container)
                layout.addWidget(QLabel("Заказы отсутствуют или произошла ошибка загрузки"))
                self.scroll_area.setWidget(container)
                return
                
            container = self.create_orders_cards_from_list(orders_data)
            
            # Устанавливаем новый контейнер
            self.scroll_area.setWidget(container)
            
            # Принудительное обновление
            self.scroll_area.update()
            self.update()
            
        except Exception as e:
            print(f"Критическая ошибка в update_orders_display: {e}")
            import traceback
            traceback.print_exc()

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
        order_card.setFixedHeight(180)  # Установили фиксированную высоту
        order_card.setMinimumHeight(180)  # Минимальная высота
        order_card.setMaximumHeight(200)  # Максимальная высота
        
        # Получаем артикул заказа из состава заказа (берем первый товар)
        order_items = self.database.get_order_items(order['id'])
        article = ""
        if order_items:
            article = order_items[0]['article'] if order_items[0]['article'] else f"ORD{order['id']}"
        else:
            article = f"ORD{order['id']}"
        
        # Делаем всю карточку кликабельной для всех ролей
        order_card.setCursor(Qt.CursorShape.PointingHandCursor)
        order_card.mousePressEvent = lambda e, oid=order['id']: self.on_order_card_clicked(oid, e)
        
        order_card_hbox = QHBoxLayout(order_card)
        order_card_hbox.setContentsMargins(10, 10, 10, 10)
        order_card_hbox.setSpacing(15)

        # Основная информация о заказе (левая часть)
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)

        # 1. Артикул заказа (берем из состава заказа)
        article_label = QLabel(f"Артикул: {article}")
        article_label.setObjectName("cardText")
        article_label.setStyleSheet("font-weight: bold; font-size: 20px;")
        info_layout.addWidget(article_label)

        # 2. Статус заказа (простым текстом, сразу под артикулом)
        status_label = QLabel(f"Статус: {order['status']}")
        status_label.setObjectName("cardText")
        status_label.setStyleSheet("font-size: 18px;")
        info_layout.addWidget(status_label)

        # 3. Адрес пункта выдачи
        pvz_address = self.database.take_pvz_address(order['pvz'])
        address_label = QLabel(f"Адрес: {pvz_address}")
        address_label.setObjectName("cardText")
        address_label.setStyleSheet("font-size: 18px;")
        address_label.setWordWrap(True)
        info_layout.addWidget(address_label)

        # 4. Дата заказа
        date_label = QLabel(f"Дата заказа: {order['create_date']}")
        date_label.setObjectName("cardText")
        date_label.setStyleSheet("font-size: 18px;")
        info_layout.addWidget(date_label)

        # Добавляем основную информацию
        order_card_hbox.addWidget(info_widget, 70)  # 70% ширины

        # Правая часть - дата доставки в отдельном квадрате
        delivery_widget = QWidget()
        delivery_widget.setObjectName("item_card")
        delivery_widget.setFixedWidth(150)  # Фиксированная ширина
        delivery_layout = QVBoxLayout(delivery_widget)
        delivery_layout.setContentsMargins(5, 5, 5, 5)
        delivery_layout.setSpacing(5)

        # Добавляем растягивающий элемент сверху
        delivery_layout.addStretch()

        # Контейнер для центрирования даты доставки
        date_container = QWidget()
        date_container_layout = QVBoxLayout(date_container)
        date_container_layout.setContentsMargins(0, 0, 0, 0)
        date_container_layout.setSpacing(5)
        
        # Заголовок "Дата доставки"
        delivery_title = QLabel("Дата доставки")
        delivery_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        delivery_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        date_container_layout.addWidget(delivery_title)

        # Сама дата доставки
        delivery_date = QLabel(str(order['delivery_date']))
        delivery_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        delivery_date.setStyleSheet("font-size: 20px; font-weight: bold;")
        date_container_layout.addWidget(delivery_date)
        
        # Добавляем контейнер с датой в основной layout
        date_container_layout.addStretch()
        delivery_layout.addWidget(date_container)

        # Добавляем растягивающий элемент внизу
        delivery_layout.addStretch()

        order_card_hbox.addWidget(delivery_widget, 30)  # 30% ширины

        return order_card

    def on_order_card_clicked(self, order_id, event):
        """Обработка клика по карточке заказа для всех ролей"""
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"Клик по карточке заказа: {order_id}")
            # Устанавливаем ID заказа в Storage
            Storage.set_order_id(order_id)
            
            # Очищаем кэш старого фрейма редактирования заказа
            if 'UpdateOrderFrame' in self.controller.frames_cache:
                old_frame = self.controller.frames_cache.pop('UpdateOrderFrame')
                old_frame.deleteLater()
            
            # Создаем новый фрейм с актуальными данными
            from FRAMES import UpdateOrderWindow
            self.controller.switch_window(UpdateOrderWindow.UpdateOrderFrame)

    def go_to_create_order_window(self):
        """Переход в окно создания заказа"""
        print("Переход в окно создания заказа")
        self.controller.switch_window(CreateOrderWindow.CreateOrderFrame)

    def go_back_to_home_window(self):
        if Messages.send_I_message("Вы точно хотите прекратить редактирование?", "Подтверждение выхода") < 20000:
            # Очищаем временные данные
            Storage.set_item_id(None)
            Storage.set_order_id(None)
            
            # Удаляем фреймы из кэша
            self.controller.clear_cache_except(['HomeFrame', 'LogInFrame'])
            self.controller.switch_window(HomePageWindow.HomeFrame)