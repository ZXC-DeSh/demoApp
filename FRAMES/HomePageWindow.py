from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import Messages
from FRAMES import CreateCardWindow, LogInWindow, OrdersCardsWindow, UpdateCardWindow
from FRAMES.cards import ProductCard
from FRAMES.components import create_header, create_title
from StaticStorage import Storage


class HomeFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db
        self.search_edit = None
        self.company_combo = None
        self.sort_asc_radio = None
        self.sort_desc_radio = None

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search_and_filter)

        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.frame_layout.addWidget(create_header(self.database, self.go_back_to_log_in_window))
        self.frame_layout.addWidget(create_title("Список товаров"))

        actions = set(Storage.get_roles_action())
        if "Поиск" in actions:
            self.create_search_block()
        if "Сортировка" in actions:
            self.create_sort_block()
        if "Фильтрация" in actions:
            self.create_filter_block()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.frame_layout.addWidget(self.scroll_area)
        self.update_items_display(self.database.get_all_items())

        if Storage.get_user_role() == "Администратор":
            add_button = QPushButton("Добавить товар", objectName="button")
            add_button.clicked.connect(self.open_create_product)
            self.frame_layout.addWidget(add_button)

        if "Заказы" in actions:
            orders_button = QPushButton("Заказы", objectName="button")
            orders_button.clicked.connect(
                lambda: self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)
            )
            self.frame_layout.addWidget(orders_button)

    def create_search_block(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(QLabel("Поиск:", objectName="UpdateTextHint"))
        self.search_edit = QLineEdit(objectName="search_edit")
        self.search_edit.textChanged.connect(self.on_any_change)
        layout.addWidget(self.search_edit)
        self.frame_layout.addWidget(container)

    def create_sort_block(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(QLabel("Сортировать по количеству на складе:", objectName="UpdateTextHint"))

        self.sort_asc_radio = QRadioButton("↑ Возрастание")
        self.sort_desc_radio = QRadioButton("↓ Убывание")
        self.sort_group = QButtonGroup(self)
        self.sort_group.addButton(self.sort_asc_radio)
        self.sort_group.addButton(self.sort_desc_radio)
        self.sort_asc_radio.toggled.connect(self.on_any_change)
        self.sort_desc_radio.toggled.connect(self.on_any_change)
        layout.addWidget(self.sort_asc_radio)
        layout.addWidget(self.sort_desc_radio)
        layout.addStretch()
        self.frame_layout.addWidget(container)

    def create_filter_block(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(QLabel("Поставщик:", objectName="UpdateTextHint"))
        self.company_combo = QComboBox(objectName="company_filter")
        self.company_combo.addItems(self.database.take_all_deliveryman())
        self.company_combo.currentIndexChanged.connect(self.on_any_change)
        layout.addWidget(self.company_combo)
        layout.addStretch()
        self.frame_layout.addWidget(container)

    def on_any_change(self, *_):
        self.search_timer.start(300)

    def perform_search_and_filter(self):
        search_text = self.search_edit.text().strip() if self.search_edit else ""
        company = self.company_combo.currentText() if self.company_combo else ""
        sort_by_count = bool(
            (self.sort_asc_radio and self.sort_asc_radio.isChecked())
            or (self.sort_desc_radio and self.sort_desc_radio.isChecked())
        )
        sort_ascending = not (self.sort_desc_radio and self.sort_desc_radio.isChecked())
        try:
            items = self.database.search_and_filter_items(
                search_text=search_text,
                company_filter=company,
                sort_by_count=sort_by_count,
                sort_ascending=sort_ascending,
            )
            self.update_items_display(items)
        except Exception as error:
            Messages.show_error(f"Не удалось обновить список товаров: {error}")

    def update_items_display(self, items):
        container = QWidget()
        layout = QVBoxLayout(container)
        if not items:
            layout.addWidget(create_title("Товары не найдены"))
        else:
            on_click = self.open_update_product if Storage.get_user_role() == "Администратор" else None
            for item in items:
                layout.addWidget(ProductCard(item, on_click))
        layout.addStretch()
        self.scroll_area.setWidget(container)

    def open_create_product(self):
        self.controller.invalidate_frame(CreateCardWindow.CreateCardFrame)
        self.controller.switch_window(CreateCardWindow.CreateCardFrame)

    def open_update_product(self, item_id):
        Storage.set_item_id(item_id)
        self.controller.invalidate_frame(UpdateCardWindow.UpdateCardFrame)
        self.controller.switch_window(UpdateCardWindow.UpdateCardFrame)

    def go_back_to_log_in_window(self):
        if not Messages.ask_confirmation(
            "Выйти из учётной записи и вернуться к окну входа?",
            "Выход из системы",
        ):
            return
        Storage.clear_all()
        self.controller.clear_cache_except(["LogInFrame"])
        self.controller.switch_window(LogInWindow.LogInFrame)
