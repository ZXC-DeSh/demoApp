import os
import re
import shutil
import tempfile
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget

import Messages
from FRAMES.components import ICONS_DIR, PROJECT_ROOT


class ProductImageEditor(QWidget):
    """Выбор, предпросмотр и сохранение изображения товара размером до 300x200."""

    SIZE = (300, 200)
    TEMP_DIR = PROJECT_ROOT / "temp"

    def __init__(self, initial_filename: str = "", button_text: str = "Добавить фото"):
        super().__init__()
        ICONS_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.initial_filename = initial_filename or "picture.png"
        self.selected_path: Path | None = None

        layout = QVBoxLayout(self)
        self.preview = QLabel(objectName="product_image_preview")
        self.preview.setFixedSize(*self.SIZE)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)

        button = QPushButton(button_text, objectName="button")
        button.clicked.connect(self.select_image)
        layout.addWidget(button)
        self._show_path(ICONS_DIR / self.initial_filename)

    def select_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фото",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if not file_path:
            return
        try:
            self.cleanup()
            self.selected_path = self._prepare_image(Path(file_path))
            self._show_path(self.selected_path)
        except Exception as error:
            Messages.show_error(f"Не удалось обработать изображение: {error}")

    def _prepare_image(self, source: Path) -> Path:
        with Image.open(source) as image:
            image = image.convert("RGB")
            image.thumbnail(self.SIZE, Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", self.SIZE, "white")
            offset = ((self.SIZE[0] - image.width) // 2, (self.SIZE[1] - image.height) // 2)
            canvas.paste(image, offset)

            handle, temp_name = tempfile.mkstemp(suffix=".jpg", dir=self.TEMP_DIR)
            os.close(handle)
            canvas.save(temp_name, quality=90)
            return Path(temp_name)

    def _show_path(self, path: Path) -> None:
        target = path if path.exists() else ICONS_DIR / "picture.png"
        pixmap = QPixmap(str(target))
        if pixmap.isNull():
            self.preview.setText("Нет фото")
            self.preview.setPixmap(QPixmap())
            return
        self.preview.setPixmap(
            pixmap.scaled(
                *self.SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def save(self, article: str, old_filename: str = "") -> str:
        if not self.selected_path:
            return old_filename or self.initial_filename or "picture.png"

        safe_article = re.sub(r"[^\w.-]+", "_", article, flags=re.UNICODE).strip("._")
        filename = f"{safe_article or 'product'}.jpg"
        destination = ICONS_DIR / filename
        staged = destination.with_name(f".{destination.name}.tmp")

        shutil.copy2(self.selected_path, staged)
        os.replace(staged, destination)
        self.initial_filename = filename
        self.cleanup()
        self._show_path(destination)
        return filename

    @staticmethod
    def delete(filename: str) -> None:
        if filename and filename != "picture.png":
            path = ICONS_DIR / Path(filename).name
            if path.exists():
                path.unlink()

    def cleanup(self) -> None:
        if self.selected_path and self.selected_path.exists():
            self.selected_path.unlink()
        self.selected_path = None
