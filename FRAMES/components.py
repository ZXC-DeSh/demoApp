from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = PROJECT_ROOT / "ICONS"


def create_logo_label(size: int = 120) -> QLabel:
    """Возвращает логотип из ресурсов без изменения его пропорций."""
    label = QLabel()
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFixedSize(size, size)

    logo_path = next(
        (ICONS_DIR / name for name in ("logo.JPG", "logo.png") if (ICONS_DIR / name).exists()),
        None,
    )
    if logo_path:
        pixmap = QPixmap(str(logo_path)).scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        label.setPixmap(pixmap)
    else:
        label.setText("ОБУВЬ")
        label.setObjectName("text_logo")
    return label


def create_header(database, on_back) -> QWidget:
    """Создаёт общую шапку: назад, логотип и ФИО пользователя."""
    header = QWidget(objectName="header_widget")
    layout = QHBoxLayout(header)

    back_button = QPushButton("< Назад", objectName="back_header_button")
    back_button.setFixedWidth(150)
    back_button.clicked.connect(on_back)
    layout.addWidget(back_button)
    layout.addStretch()
    layout.addWidget(create_logo_label())
    layout.addStretch()

    user_data = database.take_user_data() or {"user_name": "Аккаунт Гостя"}
    user_name = user_data.get("user_name") or "Аккаунт Гостя"
    layout.addWidget(QLabel(user_name.replace(" ", "\n"), objectName="FIO"))
    return header


def create_title(text: str) -> QLabel:
    title = QLabel(text, objectName="Title")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return title


def create_labeled_edit(
    label_text: str,
    value="",
    *,
    placeholder: str = "",
    read_only: bool = False,
) -> tuple[QWidget, QLineEdit]:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))

    field = QLineEdit(objectName="UpdateTextEdit")
    field.setText("" if value is None else str(value))
    field.setPlaceholderText(placeholder)
    field.setReadOnly(read_only)
    layout.addWidget(field)
    return container, field


def create_labeled_combo(
    label_text: str,
    items,
    *,
    current="",
    enabled: bool = True,
    placeholder: str = "",
) -> tuple[QWidget, QComboBox]:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))

    field = QComboBox(objectName="UpdateTextEdit")
    values = [str(item) for item in items if item is not None]
    current_text = "" if current is None else str(current)
    if current_text and current_text not in values:
        values.insert(0, current_text)
    field.addItems(values)
    field.setPlaceholderText(placeholder)
    field.setEnabled(enabled)
    if current_text:
        field.setCurrentText(current_text)
    layout.addWidget(field)
    return container, field


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            clear_layout(item.layout())

