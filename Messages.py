from PySide6.QtWidgets import QMessageBox


def _show(icon, text: str, title: str, buttons=QMessageBox.StandardButton.Ok):
    message = QMessageBox()
    message.setWindowTitle(title)
    message.setText(text)
    message.setIcon(icon)
    message.setStandardButtons(buttons)
    if buttons & QMessageBox.StandardButton.Yes:
        message.button(QMessageBox.StandardButton.Yes).setText("Да")
    if buttons & QMessageBox.StandardButton.No:
        message.button(QMessageBox.StandardButton.No).setText("Нет")
    return message.exec()


def show_info(text: str, title: str = "Информация"):
    return _show(QMessageBox.Icon.Information, text, title)


def show_warning(text: str, title: str = "Предупреждение"):
    return _show(QMessageBox.Icon.Warning, text, title)


def show_error(text: str, title: str = "Ошибка"):
    return _show(QMessageBox.Icon.Critical, text, title)


def ask_confirmation(text: str, title: str = "Подтверждение") -> bool:
    result = _show(
        QMessageBox.Icon.Question,
        text,
        title,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes