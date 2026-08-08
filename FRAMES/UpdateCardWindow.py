from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QPushButton, QScrollArea, QVBoxLayout, QWidget

import Messages
from FRAMES import HomePageWindow
from FRAMES.components import create_header, create_title
from FRAMES.image_service import ProductImageEditor
from FRAMES.product_form import ProductForm
from StaticStorage import Storage


class UpdateCardFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db
        self.item_data = self.database.take_item_single_info()
        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.frame_layout.addWidget(create_header(self.database, self.go_back_to_home_window))
        self.frame_layout.addWidget(create_title("Редактирование товара"))
        if not self.item_data:
            Messages.show_error("Выбранный товар не найден.", "Ошибка загрузки")
            return

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        layout = QVBoxLayout(container)
        self.product_form = ProductForm(self.database, self.item_data)
        self.image_editor = ProductImageEditor(
            self.item_data.get("picture", "picture.png"),
            "Изменить фото",
        )
        layout.addWidget(self.product_form)
        layout.addWidget(self.image_editor)
        scroll_area.setWidget(container)
        self.frame_layout.addWidget(scroll_area)

        save_button = QPushButton("Сохранить изменения", objectName="button")
        save_button.clicked.connect(self.save_changes)
        self.frame_layout.addWidget(save_button)

        delete_button = QPushButton("Удалить товар", objectName="button")
        delete_button.clicked.connect(self.delete_item)
        self.frame_layout.addWidget(delete_button)

    def save_changes(self):
        product = self.product_form.get_data()
        if product is None:
            return
        if self.database.article_exists(product.article, exclude_id=self.item_data["id"]):
            Messages.show_error("Товар с таким артикулом уже существует.")
            return

        old_picture = self.item_data.get("picture", "picture.png")
        try:
            new_picture = self.image_editor.save(product.article, old_picture)
        except Exception as error:
            Messages.show_error(f"Не удалось сохранить изображение: {error}")
            return

        if not self.database.update_card_picture(new_picture, product.to_dict()):
            if new_picture != old_picture:
                ProductImageEditor.delete(new_picture)
            Messages.show_error("Не удалось обновить товар в базе данных.")
            return

        if new_picture != old_picture:
            ProductImageEditor.delete(old_picture)
        Messages.show_info("Товар успешно обновлён.", "Готово")
        self.controller.invalidate_frame(HomePageWindow.HomeFrame)
        self.controller.switch_window(HomePageWindow.HomeFrame)

    def delete_item(self):
        article = self.item_data["article"]
        if self.database.check_product_in_orders(article):
            Messages.show_error(
                "Товар присутствует в заказе и не может быть удалён.",
                "Удаление запрещено",
            )
            return
        if not Messages.ask_confirmation(
            f"Удалить товар «{self.item_data['name']}»? Отменить операцию будет невозможно.",
            "Удаление товара",
        ):
            return
        if not self.database.delete_item(article):
            Messages.show_error("Не удалось удалить товар.")
            return

        ProductImageEditor.delete(self.item_data.get("picture", ""))
        Messages.show_info("Товар удалён.", "Готово")
        Storage.set_item_id(None)
        self.controller.invalidate_frame(HomePageWindow.HomeFrame)
        self.controller.switch_window(HomePageWindow.HomeFrame)

    def go_back_to_home_window(self):
        if Messages.ask_confirmation(
            "Прекратить редактирование? Несохранённые изменения будут потеряны.",
            "Подтверждение выхода",
        ):
            self.image_editor.cleanup()
            Storage.set_item_id(None)
            self.controller.switch_window(HomePageWindow.HomeFrame)
