from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

import Messages
from FRAMES.components import create_labeled_combo, create_labeled_edit


DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d")


def parse_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip().split(" ")[0]
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"Неверный формат даты: {value}")


class OrderDetailsForm(QWidget):
    STATUSES = ("Новый", "В обработке", "Завершен")

    def __init__(self, database, data: dict | None = None, editable: bool = True):
        super().__init__()
        self.database = database
        self.data = data or {}
        layout = QVBoxLayout(self)

        article = self.data.get("article", "")
        container, self.article = create_labeled_edit(
            "Артикул заказа:",
            article,
            placeholder="Сформируется из состава заказа",
            read_only=True,
        )
        layout.addWidget(container)

        statuses = list(self.STATUSES)
        current_status = self.data.get("status", "Новый")
        container, self.status = create_labeled_combo(
            "Статус заказа:",
            statuses,
            current=current_status,
            enabled=editable,
        )
        layout.addWidget(container)

        pvz_values = database.take_all_pvz_addresses()
        current_pvz = self.data.get("pvz_display", "")
        container, self.pvz = create_labeled_combo(
            "Адрес пункта выдачи:",
            pvz_values,
            current=current_pvz,
            enabled=editable,
        )
        layout.addWidget(container)

        create_value = self.data.get("create_date") or date.today().strftime("%d.%m.%Y")
        container, self.create_date = create_labeled_edit(
            "Дата заказа:",
            create_value,
            read_only=True,
        )
        layout.addWidget(container)

        delivery_value = self.data.get("delivery_date") or (date.today() + timedelta(days=3)).strftime("%d.%m.%Y")
        container, self.delivery_date = create_labeled_edit(
            "Дата выдачи:",
            delivery_value,
            placeholder="ДД.ММ.ГГГГ",
            read_only=not editable,
        )
        layout.addWidget(container)

    def set_article_from_items(self, items: list[dict]) -> None:
        self.article.setText(", ".join(f"{item['article']}, {item['quantity']}" for item in items))

    def get_data(self) -> dict | None:
        pvz_text = self.pvz.currentText().strip()
        if not pvz_text:
            Messages.show_error("Выберите пункт выдачи.")
            return None
        try:
            create_date = parse_date(self.create_date.text())
            delivery_date = parse_date(self.delivery_date.text())
            if delivery_date < create_date:
                raise ValueError("Дата выдачи не может быть раньше даты заказа.")
            pvz_id = int(pvz_text.split(" | ", 1)[0])
        except ValueError as error:
            Messages.show_error(str(error), "Некорректные данные заказа")
            return None
        return {
            "pvz_id": pvz_id,
            "status": self.status.currentText(),
            "create_date": create_date,
            "delivery_date": delivery_date,
            "article": self.article.text(),
        }


class OrderItemsView(QWidget):
    def __init__(self, items: list[dict]):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Состав заказа:", objectName="UpdateTextHint"))
        if not items:
            layout.addWidget(QLabel("Товары отсутствуют", objectName="empty_text"))
            return
        for item in items:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.addWidget(QLabel(item["name"], objectName="order_item_name"), 70)
            details = f"Арт: {item['article']}, кол-во: {item['quantity']}, цена: {item['price']} руб."
            details_label = QLabel(details, objectName="order_item_details")
            details_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            row_layout.addWidget(details_label, 30)
            layout.addWidget(row)
