from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from FRAMES.components import ICONS_DIR


def _label(text, *, object_name="cardText", word_wrap=False, alignment=None) -> QLabel:
    label = QLabel(str(text), objectName=object_name)
    label.setWordWrap(word_wrap)
    if alignment is not None:
        label.setAlignment(alignment)
    return label


class ProductCard(QWidget):
    def __init__(self, item: dict, on_click=None):
        super().__init__(objectName="item_card")
        self.setMinimumHeight(260)
        self.setMaximumHeight(300)
        state = "out_of_stock" if item["count"] == 0 else "high_discount" if item["sale"] > 15 else "normal"
        self.setProperty("state", state)

        layout = QHBoxLayout(self)
        layout.addWidget(self._picture(item.get("picture")))

        information = QPushButton() if on_click else QWidget()
        information.setObjectName("update_button" if on_click else "product_information")
        information.setMinimumHeight(240)
        if on_click:
            information.clicked.connect(lambda: on_click(item["id"]))
        info_layout = QVBoxLayout(information)

        info_layout.addWidget(_label(f"{item['category']} | {item['name']}"))
        info_layout.addWidget(_label(f"Описание товара: {item['information']}", word_wrap=True))
        info_layout.addWidget(_label(f"Производитель: {item['creator']}", word_wrap=True))
        info_layout.addWidget(_label(f"Поставщик: {item['deliveryman']}", word_wrap=True))
        info_layout.addLayout(self._price_layout(item))
        info_layout.addWidget(_label(f"Единица измерения: {item['edinica']}", word_wrap=True))
        info_layout.addWidget(_label(f"Количество на складе: {item['count']}", object_name="stock_count"))
        layout.addWidget(information)

        discount = QWidget(objectName="sale_widget")
        discount.setFixedWidth(100)
        discount_layout = QVBoxLayout(discount)
        discount_layout.addWidget(
            _label(
                f"Скидка:\n{item['sale']}%",
                object_name="sale_text",
                alignment=Qt.AlignmentFlag.AlignCenter,
            )
        )
        layout.addWidget(discount)

    @staticmethod
    def _picture(filename) -> QLabel:
        label = QLabel(objectName="product_picture")
        label.setFixedSize(120, 120)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        path = ICONS_DIR / Path(filename or "picture.png").name
        if not path.exists():
            path = ICONS_DIR / "picture.png"
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            label.setText("Нет фото")
        else:
            label.setPixmap(
                pixmap.scaled(
                    120,
                    120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        return label

    @staticmethod
    def _price_layout(item: dict) -> QHBoxLayout:
        layout = QHBoxLayout()
        cost = float(item["cost"])
        sale = float(item["sale"])
        if sale > 0:
            layout.addWidget(_label(f"Цена: {item['cost']}", object_name="original_price"))
            layout.addWidget(_label(f"{cost * (1 - sale / 100):.2f}", object_name="discounted_price"))
        else:
            layout.addWidget(_label(f"Цена: {item['cost']}", object_name="normal_price"))
            layout.addStretch()
        return layout


class OrderCard(QFrame):
    def __init__(self, order: dict, on_click):
        super().__init__(objectName="item_card")
        self.setFixedHeight(180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = lambda event: self._handle_click(event, order["id"], on_click)

        layout = QHBoxLayout(self)
        info = QWidget()
        info_layout = QVBoxLayout(info)
        article = order.get("article") or f"ORD{order['id']}"
        info_layout.addWidget(_label(f"Артикул: {article}", object_name="order_article"))
        info_layout.addWidget(_label(f"Статус: {order['status']}", object_name="order_text"))
        info_layout.addWidget(_label(f"Адрес: {order.get('pvz_address', 'Адрес не найден')}", object_name="order_text", word_wrap=True))
        info_layout.addWidget(_label(f"Дата заказа: {order['create_date']}", object_name="order_text"))
        layout.addWidget(info, 70)

        delivery = QWidget(objectName="delivery_box")
        delivery_layout = QVBoxLayout(delivery)
        delivery_layout.addStretch()
        delivery_layout.addWidget(
            _label("Дата доставки", object_name="delivery_title", alignment=Qt.AlignmentFlag.AlignCenter)
        )
        delivery_layout.addWidget(
            _label(order["delivery_date"], object_name="delivery_date", alignment=Qt.AlignmentFlag.AlignCenter)
        )
        delivery_layout.addStretch()
        layout.addWidget(delivery, 30)

    @staticmethod
    def _handle_click(event, order_id, callback) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            callback(order_id)
