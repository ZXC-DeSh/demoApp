import logging
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

import styles
from DATABASE import Database
from FRAMES import LogInWindow


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(module)s] -> %(message)s",
    datefmt="%H:%M:%S",
)


class MainApplicationClass(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обувь")
        self.setMinimumSize(600, 800)
        self.db = Database.DatabaseConnection()

        self.frame_container = QStackedWidget()
        self.setCentralWidget(self.frame_container)

        login_frame = LogInWindow.LogInFrame(self)
        self.frame_container.addWidget(login_frame)
        self.frame_container.setCurrentWidget(login_frame)
        self.frames_cache = {"LogInFrame": login_frame}

    def switch_window(self, frame_class):
        """Открывает единственный закэшированный экземпляр указанного экрана."""
        name = frame_class.__name__
        frame = self.frames_cache.get(name)
        if frame is None:
            frame = frame_class(self)
            self.frames_cache[name] = frame
            self.frame_container.addWidget(frame)
        self.frame_container.setCurrentWidget(frame)

    def invalidate_frame(self, frame_or_name) -> None:
        """Удаляет экран из кэша, чтобы при следующем открытии загрузились актуальные данные."""
        name = frame_or_name if isinstance(frame_or_name, str) else frame_or_name.__name__
        frame = self.frames_cache.pop(name, None)
        if frame is not None:
            self.frame_container.removeWidget(frame)
            frame.deleteLater()

    def clear_cache_except(self, frame_names) -> None:
        for name in list(self.frames_cache):
            if name not in frame_names:
                self.invalidate_frame(name)

    def update_cached_frame(self, frame_class) -> None:
        self.invalidate_frame(frame_class)


def main() -> int:
    application = QApplication(sys.argv)
    icon_path = Path(__file__).resolve().parent / "ICONS" / "Icon.jpg"
    if icon_path.exists():
        application.setWindowIcon(QIcon(str(icon_path)))
    application.setFont(QFont("Times New Roman"))
    application.setStyleSheet(styles.styles_sheet)

    window = MainApplicationClass()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
