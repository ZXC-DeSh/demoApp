from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLineEdit, QPushButton, QVBoxLayout

import Messages
from FRAMES import HomePageWindow
from FRAMES.components import create_labeled_edit, create_logo_label, create_title
from StaticStorage import Storage


class LogInFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.db
        self.frame_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.frame_layout.addWidget(create_logo_label(), alignment=Qt.AlignmentFlag.AlignCenter)
        self.frame_layout.addWidget(create_title("Вход в систему"))
        self.frame_layout.addStretch()

        login_container, self.login_edit = create_labeled_edit(
            "Логин",
            placeholder="Введите логин",
        )
        password_container, self.password_edit = create_labeled_edit(
            "Пароль",
            placeholder="Введите пароль",
        )
        self.login_edit.setObjectName("LogInEdit")
        self.password_edit.setObjectName("LogInEdit")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.frame_layout.addWidget(login_container)
        self.frame_layout.addWidget(password_container)

        login_button = QPushButton("Войти", objectName="button")
        login_button.clicked.connect(self.log_in)
        self.frame_layout.addWidget(login_button)

        guest_button = QPushButton("Войти как гость", objectName="button")
        guest_button.clicked.connect(self.guest_enter)
        self.frame_layout.addWidget(guest_button)

    def log_in(self):
        login = self.login_edit.text().strip()
        password = self.password_edit.text()
        if not login or not password:
            Messages.show_warning("Введите логин и пароль.", "Не заполнены поля")
            return

        Storage.clear_all()
        if not self.database.check_user_login_password(login, password):
            Messages.show_error(
                "Пользователь не найден. Проверьте логин и пароль и повторите попытку.",
                "Ошибка авторизации",
            )
            return
        self._open_home()

    def guest_enter(self):
        Storage.clear_all()
        Storage.set_user_role("Гость")
        Storage.set_user_login("guest")
        self._open_home()

    def _open_home(self):
        self.controller.invalidate_frame(HomePageWindow.HomeFrame)
        self.controller.switch_window(HomePageWindow.HomeFrame)
