from PySide6.QtWidgets import (QApplication,
                               QMainWindow, QStackedWidget)
import sys
from DATABASE import Database
import styles
import os
from PySide6.QtGui import QIcon

# Добавление класса с фреймом авторизации
from FRAMES import LogInWindow


class MainApplicationClass(QMainWindow):
    def __init__(self):
        # Подключение конструктора от "Родителя"
        super().__init__()
        # Установка названия Приложения
        self.setWindowTitle("Обувь")

        # Установка размеров окна
        self.setMinimumSize(600, 800)

        # Создание подключения к базе данных
        self.db = Database.DatabaseConnection()

        # Объявление первого фрейма - передаем self как controller
        log_in_frame = LogInWindow.LogInFrame(controller=self)

        self.frame_container = QStackedWidget()
        # Добавление первого фрейма в контейнер (чтобы он выводился при запуске окна)
        self.frame_container.addWidget(log_in_frame)
        # Расположит self.frame_container по середине окна
        self.setCentralWidget(self.frame_container)

        # Словарь для хранения созданных фреймов
        self.frames_cache = {}

    def switch_window(self, goal_frame):
        """
        Метод смены окно в self.frame_container
        :param goal_frame: Название класса следующего фрейма
        :return: none
        """
        frame_class_name = goal_frame.__name__
        
        # Если фрейм уже создан, используем его из кэша
        if frame_class_name in self.frames_cache:
            frame = self.frames_cache[frame_class_name]
        else:
            # Создаем новый фрейм и сохраняем в кэш
            frame = goal_frame(self)
            self.frames_cache[frame_class_name] = frame
            self.frame_container.addWidget(frame)
        
        # Устанавливаем текущий фрейм
        self.frame_container.setCurrentWidget(frame)




application = QApplication(sys.argv)

# Устанавливаем иконку для всего приложения
try:
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_file_dir, "ICONS", "Icon.jpg")
    
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        # Устанавливаем иконку для всего приложения
        application.setWindowIcon(app_icon)
        print(f"Иконка приложения установлена: {icon_path}")
    else:
        print(f"Иконка не найдена по пути: {icon_path}")
except Exception as e:
    print(f"Ошибка установки иконки приложения: {e}")

# Подключение всех стилей
application.setFont("Times New Roman")  # Установка шрифта для ВСЕГО приложения
application.setStyleSheet(styles.styles_sheet)  # Установка стилей для приложения

# Вызов главного класса для запуска приложения
main_class = MainApplicationClass()
main_class.show()  # Демонстрация приложения
application.exec()  # Запуск работы приложения в системе