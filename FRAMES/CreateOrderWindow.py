from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import Messages
from FRAMES import OrdersCardsWindow
from FRAMES.components import create_header, create_title
from FRAMES.order_form import OrderDetailsForm


class CreateOrderFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db
        self.order_items = []
        self.available_products = []
        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.frame_layout.addWidget(create_header(self.database, self.go_back_to_orders_window))
        self.frame_layout.addWidget(create_title("Создание нового заказа"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        self.form_layout = QVBoxLayout(container)
        self.details_form = OrderDetailsForm(self.database)
        self.form_layout.addWidget(self.details_form)
        self.create_products_section()
        self.create_order_items_table()
        scroll.setWidget(container)
        self.frame_layout.addWidget(scroll)

        save_button = QPushButton("Создать заказ", objectName="button")
        save_button.clicked.connect(self.create_order)
        self.frame_layout.addWidget(save_button)

    def create_products_section(self):
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.addWidget(QLabel("Добавление товаров:", objectName="UpdateTextHint"))

        row = QWidget()
        row_layout = QGridLayout(row)
        row_layout.addWidget(QLabel("Товар:"), 0, 0)
        self.product_combo = QComboBox(objectName="UpdateTextEdit")
        row_layout.addWidget(self.product_combo, 0, 1, 1, 2)
        row_layout.addWidget(QLabel("Количество:"), 1, 0)
        self.quantity_input = QLineEdit("1", objectName="UpdateTextEdit")
        self.quantity_input.setFixedWidth(100)
        row_layout.addWidget(self.quantity_input, 1, 1)
        add_button = QPushButton("Добавить", objectName="small_button")
        add_button.clicked.connect(self.add_product_to_order)
        row_layout.addWidget(add_button, 1, 2)
        layout.addWidget(row)
        self.form_layout.addWidget(section)
        self.load_available_products()

    def load_available_products(self):
        self.available_products = self.database.get_all_items()
        self.product_combo.clear()
        for product in self.available_products:
            text = f"{product['article']} - {product['name']} (остаток: {product['count']})"
            self.product_combo.addItem(text, product["article"])

    def create_order_items_table(self):
        self.form_layout.addWidget(QLabel("Товары в заказе:", objectName="UpdateTextHint"))
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(
            ["Артикул", "Наименование", "Количество", "Доступно", "Действия"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.setMaximumHeight(300)
        self.form_layout.addWidget(self.items_table)

    def add_product_to_order(self):
        article = self.product_combo.currentData()
        product = next((item for item in self.available_products if item["article"] == article), None)
        if product is None:
            Messages.show_error("Выберите товар.")
            return
        if any(item["article"] == article for item in self.order_items):
            Messages.show_warning("Этот товар уже добавлен в заказ.")
            return
        try:
            quantity = int(self.quantity_input.text())
        except ValueError:
            Messages.show_error("Количество должно быть целым числом.")
            return
        if quantity <= 0 or quantity > product["count"]:
            Messages.show_error(
                f"Укажите количество от 1 до {product['count']}.",
                "Недостаточно товара",
            )
            return

        self.order_items.append(
            {
                "article": article,
                "name": product["name"],
                "quantity": quantity,
                "available": product["count"],
            }
        )
        self.quantity_input.setText("1")
        self.update_order_items_table()
        self.details_form.set_article_from_items(self.order_items)

    def update_order_items_table(self):
        self.items_table.setRowCount(len(self.order_items))
        for row, item in enumerate(self.order_items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item["article"]))
            self.items_table.setItem(row, 1, QTableWidgetItem(item["name"]))
            for column, key in ((2, "quantity"), (3, "available")):
                cell = QTableWidgetItem(str(item[key]))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.items_table.setItem(row, column, cell)
            delete_button = QPushButton("Удалить", objectName="table_button")
            delete_button.clicked.connect(lambda _, index=row: self.remove_product_from_order(index))
            self.items_table.setCellWidget(row, 4, delete_button)

    def remove_product_from_order(self, row_index):
        if 0 <= row_index < len(self.order_items):
            self.order_items.pop(row_index)
            self.update_order_items_table()
            self.details_form.set_article_from_items(self.order_items)

    def create_order(self):
        details = self.details_form.get_data()
        if details is None or not self._validate_items():
            return
        user = self.database.take_user_data() or {"user_name": "Аккаунт Гостя"}
        details.update(
            {
                "client_name": user["user_name"],
                "code": self.database.get_next_order_code(),
                "items": self.order_items,
            }
        )
        if not self.database.create_new_order(details):
            Messages.show_error("Не удалось создать заказ в базе данных.")
            return

        Messages.show_info("Заказ успешно создан.", "Готово")
        self.controller.invalidate_frame(OrdersCardsWindow.OrdersCardsFrame)
        self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)

    def _validate_items(self) -> bool:
        if not self.order_items:
            Messages.show_error("Добавьте хотя бы один товар в заказ.")
            return False
        current_products = {item["article"]: item for item in self.database.get_all_items()}
        for item in self.order_items:
            product = current_products.get(item["article"])
            if product is None or item["quantity"] > product["count"]:
                Messages.show_error(
                    f"Остаток товара «{item['name']}» изменился. Обновите состав заказа.",
                    "Недостаточно товара",
                )
                return False
        return True

    def go_back_to_orders_window(self):
        if Messages.ask_confirmation(
            "Прекратить создание заказа? Несохранённые данные будут потеряны.",
            "Подтверждение выхода",
        ):
            self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)
