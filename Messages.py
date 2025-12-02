from PySide6.QtWidgets import QMessageBox

def send_I_message(text: str, title: str = "Информация"):
    """
    Отправка информационного сообщения
    :param text: Текст сообщения
    :param title: Заголовок окна (по умолчанию "Информация")
    """
    msg = QMessageBox()
    msg.setWindowTitle(title)  # Устанавливаем заголовок
    msg.setText(text)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    result = msg.exec()
    print(f"Результат диалога: {result}")
    return result

def send_W_message(text: str, title: str = "Предупреждение"):
    """
    Отправка предупреждающего сообщения
    :param text: Текст сообщения
    :param title: Заголовок окна (по умолчанию "Предупреждение")
    """
    msg = QMessageBox()
    msg.setWindowTitle(title)  # Устанавливаем заголовок
    msg.setText(text)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()

def send_C_message(text: str, title: str = "Ошибка"):
    """
    Отправка сообщения об ошибке
    :param text: Текст сообщения
    :param title: Заголовок окна (по умолчанию "Ошибка")
    """
    msg = QMessageBox()
    msg.setWindowTitle(title)  # Устанавливаем заголовок
    msg.setText(text)
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()