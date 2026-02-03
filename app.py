from PySide6.QtWidgets import (QApplication,
                               QMainWindow, QStackedWidget)
import sys
from DATABASE import Database
import styles
import os
from PySide6.QtGui import QIcon
import logging

# Настройка логирования для интеграционных тестов
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(module)s] → %(message)s',
    datefmt='%H:%M:%S'
)

# Добавление класса с фреймом авторизации
from FRAMES import LogInWindow


class MainApplicationClass(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обувь")
        self.setMinimumSize(600, 800)
        
        logging.info("Инициализация главного приложения")
        self.db = Database.DatabaseConnection()
        
        log_in_frame = LogInWindow.LogInFrame(controller=self)        
        self.frame_container = QStackedWidget()
        self.frame_container.addWidget(log_in_frame)
        self.setCentralWidget(self.frame_container)        
        self.frames_cache = {}
    
    def switch_window(self, goal_frame):
        """
        Метод смены окно в self.frame_container
        :param goal_frame: Название класса следующего фрейма
        :return: none
        """
        frame_class_name = goal_frame.__name__
        
        logging.info(f"Запрос на переключение окна: {frame_class_name}")
        
        # Если фрейм уже создан, используем его из кэша
        if frame_class_name in self.frames_cache:
            frame = self.frames_cache[frame_class_name]
            logging.info(f"Используется закэшированный фрейм: {frame_class_name}")
        else:
            # Создаем новый фрейм и сохраняем в кэш
            logging.info(f"Создание нового фрейма: {frame_class_name}")
            frame = goal_frame(self)
            self.frames_cache[frame_class_name] = frame
            self.frame_container.addWidget(frame)
        
        # Устанавливаем текущий фрейм
        self.frame_container.setCurrentWidget(frame)
        logging.info(f"Окно переключено на: {frame_class_name}")
    
    def clear_cache_except(self, frame_names):
        """Очищает кэш фреймов, кроме указанных"""
        frames_to_remove = []
        for name, frame in self.frames_cache.items():
            if name not in frame_names:
                frames_to_remove.append(name)
        
        for name in frames_to_remove:
            frame = self.frames_cache.pop(name)
            self.frame_container.removeWidget(frame)
            frame.deleteLater()
            logging.info(f"Удален фрейм из кэша: {name}")
    
    def update_cached_frame(self, frame_class):
        """Обновляет конкретный фрейм в кэше"""
        frame_class_name = frame_class.__name__
        if frame_class_name in self.frames_cache:
            old_frame = self.frames_cache.pop(frame_class_name)
            self.frame_container.removeWidget(old_frame)
            old_frame.deleteLater()
            logging.info(f"Обновлен фрейм в кэше: {frame_class_name}")

application = QApplication(sys.argv)

# Устанавливаем иконку для всего приложения
try:
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_file_dir, "ICONS", "Icon.jpg")
    
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        # Устанавливаем иконку для всего приложения
        application.setWindowIcon(app_icon)
        logging.info(f"Иконка приложения установлена: {icon_path}")
    else:
        logging.warning(f"Иконка не найдена по пути: {icon_path}")
except Exception as e:
    logging.error(f"Ошибка установки иконки приложения: {e}")

# Подключение всех стилей
application.setFont("Times New Roman")  # Установка шрифта для ВСЕГО приложения
application.setStyleSheet(styles.styles_sheet)  # Установка стилей для приложения
logging.info("Стили приложения установлены")

# Вызов главного класса для запуска приложения
logging.info("Запуск главного окна приложения")
main_class = MainApplicationClass()
main_class.show()  # Демонстрация приложения
logging.info("Приложение запущено и отображено")
application.exec()  # Запуск работы приложения в системе