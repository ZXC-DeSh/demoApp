from PySide6.QtWidgets import (QFrame, QPushButton, QHBoxLayout, QScrollArea,
                               QFileDialog, QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QComboBox, QMessageBox)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PIL import Image
import Messages
from FRAMES import HomePageWindow
from StaticStorage import Storage
import os
import shutil
import time
import logging


class CreateCardFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db

        # Получаем путь к папке ICONS динамически
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_file_dir)  # Поднимаемся из FRAMES в корень
        self.ICONS_DIR = os.path.join(project_root, "ICONS")
        
        # Создаем папку ICONS если она не существует
        if not os.path.exists(self.ICONS_DIR):
            os.makedirs(self.ICONS_DIR)
            print(f"Создана папка для изображений: {self.ICONS_DIR}")
        
        self.new_picture_path = None
        self.input_fields = {}  # Храним ссылки на поля ввода

        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        """Генерация интерфейса"""
        # Проверяем права доступа
        if Storage.get_user_role() != "Администратор":
            Messages.send_C_message("Недостаточно прав для создания товаров!", 
                                  "Ошибка доступа")
            self.controller.switch_window(HomePageWindow.HomeFrame)
            return

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

        # ЛОГОТИП по центру
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Загружаем логотип
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_file_dir)
        logo_path = os.path.join(project_root, "ICONS", "logo.png")
        
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            # Масштабируем логотип до нужного размера
            logo_pixmap = logo_pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            # Если файл не найден, показываем текстовый логотип
            logo_label.setText("ОБУВЬ")
            logo_label.setStyleSheet("font-size: 28px; font-weight: bold; color: black;")
        
        header_widget_hbox.addWidget(logo_label)

        # Растягивающий элемент
        header_widget_hbox.addStretch()

        user_data = self.database.take_user_data()
        fio_widget = QWidget()
        fio_layout = QVBoxLayout(fio_widget)
        fio_layout.addWidget(QLabel(user_data["user_name"].replace(" ", "\n"), objectName="FIO"))
        header_widget_hbox.addWidget(fio_widget)

        self.frame_layout.addWidget(header_widget)
        
        title = QLabel("Создание товара")
        title.setObjectName("Title")
        self.frame_layout.addWidget(title)

        # Поля ввода
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.edits_container = QWidget()
        self.container_layout = QVBoxLayout(self.edits_container)
        
        self.create_input_fields()
        scroll_area.setWidget(self.edits_container)
        self.frame_layout.addWidget(scroll_area)

        # Фото
        self.picture_label = QLabel()
        self.picture_label.setFixedSize(300, 200)  # Размер 300x200 для отображения
        self.picture_label.setStyleSheet("border: 1px solid gray;")
        self.picture_label.setText("Фото не выбрано")
        self.picture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_layout.addWidget(self.picture_label)

        change_photo_button = QPushButton("Добавить фото")
        change_photo_button.clicked.connect(self.select_new_photo)
        change_photo_button.setObjectName("button")
        self.frame_layout.addWidget(change_photo_button)

        save_btn = QPushButton("Создать товар")
        save_btn.setObjectName("button")
        save_btn.clicked.connect(self.save_new_product)
        self.frame_layout.addWidget(save_btn)


    def create_input_fields(self):
        """Создает поля для ввода данных в порядке как в таблице БД"""
        fields = [
            ("article", "Артикул товара", "Укажите артикул", False),
            ("name", "Наименование товара", "Укажите наименование", False),
            ("unit", "Единица измерения", "шт.", False),
            ("cost", "Стоимость товара", "0.00", False),
            ("deliveryman", "Поставщик", "Выберите поставщика", True),
            ("creator", "Производитель", "Выберите производителя", True),
            ("category", "Категория товара", "Выберите категорию", True),
            ("sale", "Скидка (%)", "0", False),
            ("count", "Количество на складе", "0", False),
            ("information", "Описание товара", "Введите описание", False)
        ]

        self.input_fields = {}
        
        for field in fields:
            key, label, placeholder, is_combo = field
            
            if is_combo:
                widget, field_widget = self.create_combo_field(label, placeholder, self.get_combo_data(key))
            else:
                widget, field_widget = self.create_input_field(label, placeholder)
            
            self.input_fields[key] = field_widget
            self.container_layout.addWidget(widget)

        return widget

    def create_input_field(self, label_text, placeholder):
        """Создает поле ввода и возвращает (виджет, поле_ввода)"""
        widget = QWidget()
        widget.setFixedHeight(80)
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setObjectName("UpdateTextEdit")
        layout.addWidget(edit)
        return widget, edit

    def create_combo_field(self, label_text, placeholder, items):
        """Создает комбобокс и возвращает (виджет, комбобокс)"""
        widget = QWidget()
        widget.setFixedHeight(80)
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(label_text, objectName="UpdateTextHint"))
        combo = QComboBox()
        combo.setPlaceholderText(placeholder)
        combo.addItems([""] + items)
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

    def select_new_photo(self):
        """Выбор нового фото"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "", 
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            try:
                with Image.open(file_path) as img:
                    # Проверяем и изменяем размер изображения до 300x200
                    if img.size != (300, 200):
                        img = img.resize((300, 200), Image.Resampling.LANCZOS)
                        
                        # Сохраняем во временный файл с правильным размером
                        temp_dir = os.path.join(os.path.dirname(self.ICONS_DIR), "temp")
                        if not os.path.exists(temp_dir):
                            os.makedirs(temp_dir)
                        temp_path = os.path.join(temp_dir, "temp_resized_image.jpg")
                        img.save(temp_path, quality=85)
                        
                        self.new_picture_path = temp_path
                    else:
                        self.new_picture_path = file_path
                
                # Показываем превью
                pixmap = QPixmap(self.new_picture_path)
                self.picture_label.setPixmap(pixmap.scaled(
                    300, 200, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                
            except Exception as e:
                Messages.send_C_message(f"Ошибка обработки изображения: {str(e)}", "Ошибка")
                return

    def save_new_product(self):
        """Создает новый товар"""
        try:
            # Собираем данные
            user_input = self.collect_input_data()
            if not user_input:
                return

            # Проверяем уникальность артикула
            if not self.check_article_unique(user_input[0]):
                Messages.send_C_message("Товар с таким артикулом уже существует!", 
                                      "Ошибка создания")
                return

            # Обрабатываем фото
            picture_name = "picture.png"  # По умолчанию заглушка
            if self.new_picture_path:
                # Получаем расширение файла
                _, ext = os.path.splitext(self.new_picture_path)
                if not ext or ext == '':
                    ext = '.jpg'
                
                # Создаем имя файла на основе артикула
                article = user_input[0]
                picture_name = f"{article}{ext}"
                new_full_path = os.path.join(self.ICONS_DIR, picture_name)

                # Копируем новое фото
                try:
                    shutil.copy2(self.new_picture_path, new_full_path)
                    print(f"Сохранено фото товара: {new_full_path}")
                    
                    # Удаляем временный файл если он был создан
                    if "temp" in self.new_picture_path:
                        os.remove(self.new_picture_path)
                        
                except Exception as e:
                    Messages.send_C_message(f"Ошибка сохранения фото: {str(e)}", "Ошибка")
                    return

            # Сохраняем в БД
            if self.database.create_new_card(user_input, picture_name):
                # Обновляем список в главном окне
                self.refresh_home_window_items()
                
                Messages.send_I_message("Товар успешно создан!", "Успех")
                
                # Задержка перед переходом
                from PySide6.QtCore import QTimer
                QTimer.singleShot(300, lambda: self.controller.switch_window(HomePageWindow.HomeFrame))
            else:
                Messages.send_C_message("Ошибка создания товара!", "Ошибка")

        except Exception as e:
            Messages.send_C_message(f"Ошибка создания товара: {str(e)}", "Ошибка создания")

    def refresh_home_window_items(self):
        """Обновляет список товаров в главном окне"""
        try:
            # Получаем существующий фрейм главной страницы из кэша
            home_frame = self.controller.frames_cache.get('HomeFrame')
            if home_frame:
                # Обновляем отображение товаров
                items = self.database.get_all_items()
                home_frame.update_items_display(items)
                print("Главное окно обновлено после создания товара")
        except Exception as e:
            print(f"Ошибка обновления главного окна: {e}")

    def collect_input_data(self):
        """Собирает и валидирует данные из полей ввода в ПРАВИЛЬНОМ порядке для БД"""
        data = []
        
        # 1. Артикул (item_article)
        article_field = self.input_fields['article']
        article = article_field.text().strip()
        if not article:
            article = f"ART_{int(time.time()) % 1000000}"
        data.append(article)

        # 2. Наименование (item_name)
        name_field = self.input_fields['name']
        name = name_field.text().strip()
        if not name:
            Messages.send_C_message("Введите наименование товара!", "Обязательное поле")
            return None
        data.append(name)

        # 3. Единица измерения (item_edinica)
        unit_field = self.input_fields['unit']
        unit = unit_field.text().strip() if isinstance(unit_field, QLineEdit) else unit_field.currentText()
        if not unit:
            Messages.send_C_message("Введите единицу измерения!", "Обязательное поле")
            return None
        data.append(unit)

        # 4. Стоимость (item_cost)
        cost_field = self.input_fields['cost']
        cost_text = cost_field.text().strip()
        try:
            cost = float(cost_text.replace(',', '.')) if cost_text else 0.0
            if cost < 0:
                Messages.send_C_message("Стоимость не может быть отрицательной!", "Ошибка")
                return None
            data.append(str(cost))
        except ValueError:
            Messages.send_C_message("Введите корректную стоимость!", "Ошибка")
            return None

        # 5. Поставщик (item_deliveryman) ← ВАЖНО: это 5-я позиция!
        deliveryman_field = self.input_fields['deliveryman']
        deliveryman = deliveryman_field.currentText() if isinstance(deliveryman_field, QComboBox) else deliveryman_field.text()
        if not deliveryman:
            Messages.send_C_message("Выберите поставщика!", "Обязательное поле")
            return None
        data.append(deliveryman)

        # 6. Производитель (item_creator)
        creator_field = self.input_fields['creator']
        creator = creator_field.currentText() if isinstance(creator_field, QComboBox) else creator_field.text()
        if not creator:
            Messages.send_C_message("Выберите производителя!", "Обязательное поле")
            return None
        data.append(creator)

        # 7. Категория (item_category)
        category_field = self.input_fields['category']
        category = category_field.currentText() if category_field.currentText() else ""
        if not category:
            Messages.send_C_message("Выберите категорию товара!", "Обязательное поле")
            return None
        data.append(category)

        # 8. Скидка (item_sale) ← ВАЖНО: это 8-я позиция и должно быть ЧИСЛО!
        sale_field = self.input_fields['sale']
        sale_text = sale_field.text().strip()
        try:
            # Убираем символ % если пользователь его ввел
            sale_text = sale_text.replace('%', '').strip()
            sale = int(sale_text) if sale_text else 0
            if sale < 0 or sale > 100:
                Messages.send_C_message("Скидка должна быть от 0 до 100%!", "Ошибка")
                return None
            data.append(str(sale))
        except ValueError:
            Messages.send_C_message("Введите корректное значение скидки (целое число от 0 до 100)!", "Ошибка")
            return None

        # 9. Количество (item_count)
        count_field = self.input_fields['count']
        count_text = count_field.text().strip()
        try:
            count = int(count_text) if count_text else 0
            if count < 0:
                Messages.send_C_message("Количество не может быть отрицательным!", "Ошибка")
                return None
            data.append(str(count))
        except ValueError:
            Messages.send_C_message("Введите корректное количество!", "Ошибка")
            return None

        # 10. Описание (item_information)
        info_field = self.input_fields['information']
        information = info_field.text().strip()
        if not information:
            information = "Описание отсутствует"
        data.append(information)

        # Отладка: выводим собранные данные
        logging.info(f"Собранные данные для создания товара:")
        field_names = [
            "Артикул", "Наименование", "Единица измерения", "Стоимость",
            "Поставщик", "Производитель", "Категория", "Скидка", 
            "Количество", "Описание"
        ]
        
        for i, (field_name, value) in enumerate(zip(field_names, data), 1):
            logging.info(f"{i}. {field_name}: {value}")
        
        # Проверяем количество параметров
        if len(data) != 10:
            logging.error(f"ОШИБКА: ожидается 10 параметров, получено {len(data)}")
            Messages.send_C_message(f"Ошибка: собрано {len(data)} параметров вместо 10!", "Ошибка")
            return None
        
        return data

    def check_article_unique(self, article):
        """Проверяет уникальность артикула"""
        try:
            # Проверяем в БД товар с таким артикулом
            cursor = self.database.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM Items WHERE item_article = %s", (article,))
            count = cursor.fetchone()[0]
            cursor.close()
            return count == 0
        except Exception:
            return True

    def go_back_to_home_window(self):
        if Messages.send_I_message("Вы точно хотите прекратить редактирование?", 
                                 "Подтверждение выхода") < 20000:
            # Очищаем временные данные
            Storage.set_item_id(None)
            Storage.set_order_id(None)
            self.controller.switch_window(HomePageWindow.HomeFrame)