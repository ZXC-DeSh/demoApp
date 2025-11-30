from PySide6.QtWidgets import QMessageBox

def send_I_message(text: str):
    msg = QMessageBox()
    msg.setText(text)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    result = msg.exec()
    print(result)
    return result

def send_W_message(text: str):
    msg = QMessageBox()
    msg.setText(text)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()

def send_C_message(text: str):
    msg = QMessageBox()
    msg.setText(text)
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()