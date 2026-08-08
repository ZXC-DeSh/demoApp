from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QPushButton, QScrollArea, QVBoxLayout, QWidget

import Messages
from FRAMES import OrdersCardsWindow
from FRAMES.components import create_header, create_title
from FRAMES.order_form import OrderDetailsForm, OrderItemsView
from StaticStorage import Storage


class UpdateOrderFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db
        self.order_data = self.database.get_order_by_id(Storage.get_order_id())
        self.order_items = self.database.get_order_items_with_prices(Storage.get_order_id())
        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.frame_layout.addWidget(create_header(self.database, self.go_back_to_orders_window))
        is_admin = Storage.get_user_role() == "Администратор"
        title = "Редактирование заказа" if is_admin else "Просмотр заказа"
        self.frame_layout.addWidget(create_title(title))
        if not self.order_data:
            Messages.show_error("Выбранный заказ не найден.", "Ошибка загрузки")
            return

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        layout = QVBoxLayout(container)
        self.details_form = OrderDetailsForm(self.database, self.order_data, editable=is_admin)
        layout.addWidget(self.details_form)
        layout.addWidget(OrderItemsView(self.order_items))
        layout.addStretch()
        scroll.setWidget(container)
        self.frame_layout.addWidget(scroll)

        if is_admin:
            save_button = QPushButton("Сохранить изменения", objectName="button")
            save_button.clicked.connect(self.save_changes)
            self.frame_layout.addWidget(save_button)
            delete_button = QPushButton("Удалить заказ", objectName="button")
            delete_button.clicked.connect(self.delete_order)
            self.frame_layout.addWidget(delete_button)

    def save_changes(self):
        data = self.details_form.get_data()
        if data is None:
            return
        data["id"] = self.order_data["id"]
        if not self.database.update_order_data(data):
            Messages.show_error("Не удалось обновить заказ.")
            return
        Messages.show_info("Заказ успешно обновлён.", "Готово")
        self.controller.invalidate_frame(OrdersCardsWindow.OrdersCardsFrame)
        self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)

    def delete_order(self):
        if not Messages.ask_confirmation(
            "Удалить заказ? Товары будут возвращены на склад, отменить операцию будет невозможно.",
            "Удаление заказа",
        ):
            return
        if not self.database.delete_order(self.order_data["id"]):
            Messages.show_error("Не удалось удалить заказ.")
            return
        Messages.show_info("Заказ удалён.", "Готово")
        Storage.set_order_id(None)
        self.controller.invalidate_frame(OrdersCardsWindow.OrdersCardsFrame)
        self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)

    def go_back_to_orders_window(self):
        Storage.set_order_id(None)
        self.controller.switch_window(OrdersCardsWindow.OrdersCardsFrame)
