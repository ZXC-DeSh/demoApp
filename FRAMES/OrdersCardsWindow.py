from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from FRAMES import CreateOrderWindow, HomePageWindow, UpdateOrderWindow
from FRAMES.cards import OrderCard
from FRAMES.components import create_header, create_title
from StaticStorage import Storage


class OrdersCardsFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db
        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.frame_layout.addWidget(create_header(self.database, self.go_back_to_home_window))
        self.frame_layout.addWidget(create_title("Список заказов"))

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.frame_layout.addWidget(self.scroll_area)
        self.update_orders_display()

        if Storage.get_user_role() == "Администратор":
            add_button = QPushButton("Добавить заказ", objectName="button")
            add_button.clicked.connect(self.go_to_create_order_window)
            self.frame_layout.addWidget(add_button)

    def update_orders_display(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        orders = self.database.take_all_orders_rows()
        if not orders:
            empty = QLabel("Заказы отсутствуют", objectName="empty_text")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)
        else:
            for order in orders:
                layout.addWidget(OrderCard(order, self.open_order))
        layout.addStretch()
        self.scroll_area.setWidget(container)

    def open_order(self, order_id):
        Storage.set_order_id(order_id)
        self.controller.invalidate_frame(UpdateOrderWindow.UpdateOrderFrame)
        self.controller.switch_window(UpdateOrderWindow.UpdateOrderFrame)

    def go_to_create_order_window(self):
        self.controller.invalidate_frame(CreateOrderWindow.CreateOrderFrame)
        self.controller.switch_window(CreateOrderWindow.CreateOrderFrame)

    def go_back_to_home_window(self):
        Storage.set_item_id(None)
        Storage.set_order_id(None)
        self.controller.switch_window(HomePageWindow.HomeFrame)
