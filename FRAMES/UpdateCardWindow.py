from PySide6.QtWidgets import (QFrame, QPushButton, QHBoxLayout, QScrollArea, QComboBox,
                               QFileDialog, QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QMessageBox)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PIL import Image
import Messages
from FRAMES import HomePageWindow
from StaticStorage import Storage
import os
import shutil


class UpdateCardFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db

        self.ICONS_DIR = "/home/neoleg/Documents/Demka3Kurs/Demoexam2026/ICONS"
        self.new_picture_path = None
        self.item_data = {}
        self.input_fields = {}  # Храним ссылки на поля ввода

        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        """Генерация интерфейса"""
        # Шапка
        header_widget = QWidget()
        header_widget.setObjectName("header_widget")
        header_widget_hbox = QHBoxLayout(header_widget)

        back_header_btn = QPushButton("< Назад")
        back_header_btn.setFixedWidth(150)
        back_header_btn.clicked.connect(self.go_back_to_home_window)
        back_header_btn.setObjectName("back_header_button")
        header_widget_hbox.addWidget(back_header_btn)
        header_widget_hbox.addStretch()

        user_data = self.database.take_user_data()
        fio_widget = QWidget()
        fio_layout = QVBoxLayout(fio_widget)
        fio_layout.addWidget(QLabel(user_data["user_name"].replace(" ", "\n"), objectName="FIO"))
        header_widget_hbox.addWidget(fio_widget)

        self.frame_layout.addWidget(header_widget)
        
        title = QLabel("Редактирование товара")
        title.setObjectName("Title")
        self.frame_layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.edits_container = QWidget()
        self.container_layout = QVBoxLayout(self.edits_container)
        
        scroll_area.setWidget(self.edits_container)
        self.frame_layout.addWidget(scroll_area)

        # Фото
        self.picture_label = QLabel()
        self.picture_label.setFixedSize(200, 200)
        self.picture_label.setStyleSheet("border: 1px solid gray;")
        self.frame_layout.addWidget(self.picture_label)

        change_photo_button = QPushButton("Изменить фото")
        change_photo_button.clicked.connect(self.select_new_photo)
        change_photo_button.setObjectName("button")
        self.frame_layout.addWidget(change_photo_button)

        save_btn = QPushButton("Сохранить изменения")
        save_btn.setObjectName("button")
        save_btn.clicked.connect(self.save_changes)
        self.frame_layout.addWidget(save_btn)

        delete_btn = QPushButton("Удалить товар")
        delete_btn.setObjectName("button")
        delete_btn.clicked.connect(self.delete_item)
        self.frame_layout.addWidget(delete_btn)

    def showEvent(self, event):
        """Вызывается при показе окна"""
        super().showEvent(event)
        self.load_item_data()

    def load_item_data(self):
        """Загружает данные товара"""
        try:
            self.item_data = self.database.take_item_single_info()
            if not self.item_data:
                Messages.send_C_message("Товар не найден!")
                self.go_back_to_home_window()
                return
            
            self.create_input_fields()
            self.update_picture_preview()
            
        except Exception as e:
            Messages.send_C_message(f"Ошибка загрузки данных товара: {str(e)}")

    def create_input_fields(self):
        """Создает поля для редактирования"""
        # Очищаем контейнер перед созданием новых полей
        for i in reversed(range(self.container_layout.count())): 
            widget = self.container_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        self.input_fields.clear()

        fields = [
            ("id", "ID товара", self.item_data.get('id', ''), True, False),
            ("article", "Артикул товара", self.item_data.get('article', ''), True, False),
            ("name", "Наименование товара", self.item_data.get('name', ''), False, False),
            ("category", "Категория товара", self.item_data.get('category', ''), False, True),
            ("cost", "Стоимость товара", str(self.item_data.get('cost', '')), False, False),
            ("count", "Количество на складе", str(self.item_data.get('count', '')), False, False),
            ("sale", "Скидка (%)", str(self.item_data.get('sale', '')), False, False),
            ("unit", "Единица измерения", self.item_data.get('edinica', ''), False, False),
            ("deliveryman", "Поставщик", self.item_data.get('deliveryman', ''), False, True),
            ("creator", "Производитель", self.item_data.get('creator', ''), False, True),
            ("information", "Описание товара", self.item_data.get('information', ''), False, False)
        ]

        for field in fields:
            key, label, value, readonly, is_combo = field
            
            if is_combo:
                widget, field_widget = self.create_combo_field(label, value, self.get_combo_data(key))
            else:
                widget, field_widget = self.create_input_field(label, value, readonly)
            
            self.input_fields[key] = field_widget
            self.container_layout.addWidget(widget)

    def create_input_field(self, label_text, value, readonly=False):
        """Создает поле ввода и возвращает (виджет, поле_ввода)"""
        widget = QWidget()
        widget.setFixedHeight(80)
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))
        edit = QLineEdit()
        edit.setText(str(value))
        edit.setReadOnly(readonly)
        edit.setObjectName("UpdateTextEdit")
        layout.addWidget(edit)
        return widget, edit

    def create_combo_field(self, label_text, current_value, items):
        """Создает комбобокс и возвращает (виджет, комбобокс)"""
        widget = QWidget()
        widget.setFixedHeight(80)
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))
        combo = QComboBox()
        
        # Добавляем текущее значение первым
        if current_value and current_value not in items:
            items = [current_value] + items
        elif current_value and current_value in items:
            items.remove(current_value)
            items = [current_value] + items
        else:
            items = [""] + items
            
        combo.addItems(items)
        if current_value:
            combo.setCurrentText(str(current_value))
        combo.setObjectName("UpdateTextEdit")
        layout.addWidget(combo)
        return widget, combo

    def get_combo_data(self, field_type):
        """Получает данные для выпадающих списков"""
        try:
            if field_type == "category":
                items = self.database.take_all_text_data_for_combo_box("category")
            elif field_type == "deliveryman":
                items = self.database.take_all_text_data_for_combo_box("deliveryman")
            elif field_type == "creator":
                items = self.database.take_all_text_data_for_combo_box("creator")
            else:
                items = []
            
            # Фильтруем пустые значения
            return [item for item in items if item and str(item).strip() and item != 'nan']
        except Exception as e:
            print(f"Ошибка получения данных для {field_type}: {e}")
            return []

    def update_picture_preview(self):
        """Обновляет превью фото"""
        picture_name = self.item_data.get('picture', '')
        full_path = os.path.join(self.ICONS_DIR, picture_name) if picture_name else os.path.join(self.ICONS_DIR, "picture.png")
        
        if os.path.exists(full_path):
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                self.picture_label.setPixmap(pixmap.scaled(
                    self.picture_label.width(), self.picture_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio
                ))
            else:
                self.set_placeholder_image()
        else:
            self.set_placeholder_image()

    def set_placeholder_image(self):
        """Устанавливает заглушку для изображения"""
        self.picture_label.setText("Фото не найдено")
        self.picture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def select_new_photo(self):
        """Выбор нового фото"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "", "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            # Проверяем и изменяем размер изображения
            try:
                with Image.open(file_path) as img:
                    if img.size != (300, 200):
                        img = img.resize((300, 200), Image.Resampling.LANCZOS)
                        img.save(file_path)
            except Exception as e:
                Messages.send_C_message(f"Ошибка обработки изображения: {str(e)}")
                return
            
            self.new_picture_path = file_path
            pixmap = QPixmap(file_path)
            self.picture_label.setPixmap(pixmap.scaled(
                self.picture_label.width(), self.picture_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio
            ))

    def save_changes(self):
        """Сохраняет изменения товара"""
        try:
            user_input = self.collect_input_data()
            if not user_input:
                return

            # Обрабатываем фото
            new_filename = self.item_data.get('picture', '')
            if self.new_picture_path:
                _, ext = os.path.splitext(self.new_picture_path)
                new_filename = f"{self.item_data['article']}{ext}"
                new_full_path = os.path.join(self.ICONS_DIR, new_filename)

                # Удаляем старое фото
                old_filename = self.item_data.get('picture', '')
                if old_filename and old_filename != "picture.png":
                    old_full_path = os.path.join(self.ICONS_DIR, old_filename)
                    if os.path.exists(old_full_path):
                        os.remove(old_full_path)

                # Копируем новое фото
                shutil.copy2(self.new_picture_path, new_full_path)

            # Сохраняем в БД
            if self.database.update_card_picture(new_filename, user_input):
                Messages.send_I_message("Товар успешно обновлен!")
                self.controller.switch_window(HomePageWindow.HomeFrame)
            else:
                Messages.send_C_message("Ошибка обновления товара!")

        except Exception as e:
            Messages.send_C_message(f"Ошибка сохранения: {str(e)}")

    def collect_input_data(self):
        """Собирает и валидирует данные"""
        data = []
        
        # Пропускаем ID и артикул (первые 2 поля)
        fields_to_process = list(self.input_fields.keys())[2:]
        
        for key in fields_to_process:
            field_widget = self.input_fields[key]
            
            if isinstance(field_widget, QComboBox):
                value = field_widget.currentText()
            elif isinstance(field_widget, QLineEdit):
                value = field_widget.text()
            else:
                Messages.send_C_message(f"Неизвестный тип поля: {key}")
                return None

            # Валидация числовых полей
            if key in ['cost', 'count', 'sale']:
                try:
                    if key == 'cost':
                        num_value = float(value.replace(',', '.')) if value else 0.0
                    else:
                        num_value = int(value) if value else 0
                    
                    if num_value < 0:
                        Messages.send_C_message(f"Поле '{key}' не может быть отрицательным!")
                        return None
                    data.append(str(num_value))
                except ValueError:
                    Messages.send_C_message(f"Введите корректное значение для '{key}'!")
                    return None
            else:
                if not value and key in ['name', 'category', 'unit', 'deliveryman', 'creator']:
                    Messages.send_C_message(f"Заполните поле '{key}'!")
                    return None
                data.append(value)

        return data

    def delete_item(self):
        """Удаляет товар"""
        # Проверяем, используется ли товар в заказах
        if self.database.check_product_in_orders(self.item_data['article']):
            Messages.send_C_message("Невозможно удалить товар! Он используется в заказах.")
            return

        if Messages.send_I_message("Вы точно хотите удалить этот товар?") < 20000:
            if self.database.delete_item(self.item_data['article']):
                # Удаляем фото товара
                picture_name = self.item_data.get('picture', '')
                if picture_name and picture_name != "picture.png":
                    picture_path = os.path.join(self.ICONS_DIR, picture_name)
                    if os.path.exists(picture_path):
                        os.remove(picture_path)
                
                Messages.send_I_message("Товар успешно удален!")
                self.controller.switch_window(HomePageWindow.HomeFrame)
            else:
                Messages.send_C_message("Ошибка удаления товара!")

    def go_back_to_home_window(self):
        if Messages.send_I_message("Вы точно хотите прекратить редактирование?") < 20000:
            # Очищаем временные данные
            Storage.set_item_id(None)
            Storage.set_order_id(None)
            self.controller.switch_window(HomePageWindow.HomeFrame)