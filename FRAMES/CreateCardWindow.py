from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QPushButton, QScrollArea, QVBoxLayout, QWidget

import Messages
from FRAMES import HomePageWindow
from FRAMES.components import create_header, create_title
from FRAMES.image_service import ProductImageEditor
from FRAMES.product_form import ProductForm
from StaticStorage import Storage


class CreateCardFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db
        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        if Storage.get_user_role() != "Администратор":
            Messages.show_error("Добавлять товары может только администратор.", "Недостаточно прав")
            self.controller.switch_window(HomePageWindow.HomeFrame)
            return

        self.frame_layout.addWidget(create_header(self.database, self.go_back_to_home_window))
        self.frame_layout.addWidget(create_title("Создание товара"))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        layout = QVBoxLayout(container)
        self.product_form = ProductForm(self.database)
        self.image_editor = ProductImageEditor(button_text="Добавить фото")
        layout.addWidget(self.product_form)
        layout.addWidget(self.image_editor)
        scroll_area.setWidget(container)
        self.frame_layout.addWidget(scroll_area)

        save_button = QPushButton("Создать товар", objectName="button")
        save_button.clicked.connect(self.save_new_product)
        self.frame_layout.addWidget(save_button)

    def save_new_product(self):
        product = self.product_form.get_data()
        if product is None:
            return
        if self.database.article_exists(product.article):
            Messages.show_error("Товар с таким артикулом уже существует.", "Ошибка создания")
            return

        try:
            picture_name = self.image_editor.save(product.article)
        except Exception as error:
            Messages.show_error(f"Не удалось сохранить изображение: {error}")
            return

        if not self.database.create_new_card(product.to_dict(), picture_name):
            ProductImageEditor.delete(picture_name)
            Messages.show_error("Не удалось сохранить товар в базе данных.")
            return

        Messages.show_info("Товар успешно создан.", "Готово")
        self.controller.invalidate_frame(HomePageWindow.HomeFrame)
        self.controller.switch_window(HomePageWindow.HomeFrame)

    def go_back_to_home_window(self):
        if Messages.ask_confirmation(
            "Прекратить создание товара? Несохранённые данные будут потеряны.",
            "Подтверждение выхода",
        ):
            self.image_editor.cleanup()
            self.controller.switch_window(HomePageWindow.HomeFrame)
