from dataclasses import asdict, dataclass
from time import time

from PySide6.QtWidgets import QComboBox, QLineEdit, QVBoxLayout, QWidget

import Messages
from FRAMES.components import create_labeled_combo, create_labeled_edit


@dataclass(frozen=True)
class ProductData:
    article: str
    name: str
    unit: str
    cost: float
    deliveryman: str
    creator: str
    category: str
    sale: int
    count: int
    information: str

    def to_dict(self) -> dict:
        return asdict(self)


class ProductForm(QWidget):
    """Общая форма добавления и редактирования товара."""

    FIELD_SPECS = (
        ("article", "Артикул товара", "Укажите артикул", False),
        ("name", "Наименование товара", "Укажите наименование", False),
        ("unit", "Единица измерения", "шт.", False),
        ("cost", "Стоимость товара", "0.00", False),
        ("deliveryman", "Поставщик", "Выберите поставщика", True),
        ("creator", "Производитель", "Выберите производителя", True),
        ("category", "Категория товара", "Выберите категорию", True),
        ("sale", "Скидка (%)", "0", False),
        ("count", "Количество на складе", "0", False),
        ("information", "Описание товара", "Введите описание", False),
    )
    DATA_KEYS = {"unit": "edinica"}
    REQUIRED_FIELDS = {
        "name": "наименование товара",
        "unit": "единицу измерения",
        "deliveryman": "поставщика",
        "creator": "производителя",
        "category": "категорию товара",
    }

    def __init__(self, database, data: dict | None = None):
        super().__init__()
        self.database = database
        self.editing = bool(data)
        self.fields = {}
        self.form_layout = QVBoxLayout(self)

        if self.editing:
            container, field = create_labeled_edit(
                "ID товара",
                data.get("id", ""),
                read_only=True,
            )
            self.fields["id"] = field
            self.form_layout.addWidget(container)

        for key, label, placeholder, is_combo in self.FIELD_SPECS:
            if is_combo:
                container, field = create_labeled_combo(
                    label,
                    [""] + self._combo_values(key),
                    placeholder=placeholder,
                )
            else:
                container, field = create_labeled_edit(
                    label,
                    placeholder=placeholder,
                    read_only=self.editing and key == "article",
                )
            self.fields[key] = field
            self.form_layout.addWidget(container)

        if data:
            self.load_data(data)

    def _combo_values(self, key: str) -> list[str]:
        try:
            values = self.database.take_all_text_data_for_combo_box(key)
            return [str(value) for value in values if value and str(value).strip() != "nan"]
        except Exception:
            return []

    def load_data(self, data: dict) -> None:
        for key, field in self.fields.items():
            source_key = self.DATA_KEYS.get(key, key)
            value = data.get(source_key, "")
            if isinstance(field, QComboBox):
                text = str(value)
                if text and field.findText(text) < 0:
                    field.addItem(text)
                field.setCurrentText(text)
            elif isinstance(field, QLineEdit):
                field.setText("" if value is None else str(value))

    def get_data(self) -> ProductData | None:
        values = {
            key: (field.currentText() if isinstance(field, QComboBox) else field.text()).strip()
            for key, field in self.fields.items()
            if key != "id"
        }
        values["article"] = values["article"] or f"ART_{int(time()) % 1_000_000}"

        for key, label in self.REQUIRED_FIELDS.items():
            if not values[key]:
                Messages.show_error(f"Заполните {label}.", "Обязательное поле")
                return None

        try:
            cost = float(values["cost"].replace(",", ".")) if values["cost"] else 0.0
            sale = int(values["sale"]) if values["sale"] else 0
            count = int(values["count"]) if values["count"] else 0
        except ValueError:
            Messages.show_error(
                "Стоимость, скидка и количество должны быть числами.",
                "Некорректные данные",
            )
            return None

        if cost < 0 or sale < 0 or count < 0:
            Messages.show_error(
                "Стоимость, скидка и количество не могут быть отрицательными.",
                "Некорректные данные",
            )
            return None

        return ProductData(
            article=values["article"],
            name=values["name"],
            unit=values["unit"],
            cost=cost,
            deliveryman=values["deliveryman"],
            creator=values["creator"],
            category=values["category"],
            sale=sale,
            count=count,
            information=values["information"],
        )
