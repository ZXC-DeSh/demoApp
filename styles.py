styles_sheet = """
/* Основные цвета из руководства по стилю */
QWidget {
    background-color: #FFFFFF;  /* Основной фон - белый */
    font-family: "Times New Roman";
    color: black;
}

#Title {
    font-size: 60px;
    font-weight: bold;
    color: black;
    background: none;
    qproperty-alignment: AlignCenter;
}

#logInLabel {
    font-size: 30px;
    padding-left: 15px;
    padding-bottom: 10px;
    color: black;
    background: none;
}

#LogInEdit {
    font-size: 30px;
    color: black;
    padding: 10px;
    background: white;
    border: 1px solid #cccccc;
}

#button {
    font-size: 40px;
    background: #00FA9A;  /* Акцентный цвет */
    color: black;
    border: 1px solid black;
    padding: 10px;
}

#button::hover {
    font-size: 40px;
    font-weight: bold;
    background: #00FA9A;
    color: black;
    border: 2px solid black;
    padding: 10px;
}

#FIO {
    font-size: 30px;
    qproperty-alignment: AlignRight;
    padding-right: 10px;
    color: black;
    background: none;
}

#back_header_button {
    font-size: 30px;
    color: black;
    background: #7FFF00;  /* Дополнительный фон */
    border: none;
    padding: 20px;
}

#back_header_button::hover {
    font-size: 30px;
    color: black;
    font-weight: bold;
    background: #7FFF00;
    border: none;
    padding: 20px;
}

#header_widget {
    background: #7FFF00;  /* Дополнительный фон */
    border: 1px solid black;
}

#header_widget QWidget {
    background: none;
    border: none;
}

#sale_widget {
    border: 1px solid black;
    background: white;
    color: black;
}

#cardText {
    font-size: 20px;
    color: black;  /* Черный текст для читаемости */
    background: none;
}

#sale_count {
    qproperty-alignment: AlignCenter;
    font-size: 20px;
    color: black;
    background: none;
}

#search_edit {
    font-size: 20px;
    padding: 10px;
    color: black;
    border: 1px solid black;
    background: white;
}

#search_button {
    font-size: 20px;
    border: none;
    background: #00FA9A;  /* Акцентный цвет */
    color: black;
    padding: 10px;
}

#search_button::hover {
    font-size: 20px;
    border: 1px solid black;
    background: #00FA9A;
    color: black;
    padding: 10px;
}

#item_card {
    border: 3px solid black;
    background: white;  /* Белый фон карточек по умолчанию */
}

#update_button {
    border: 1px solid black;
    background: white;
    color: black;
}

#UpdateTextEdit {
    font-size: 20px;
    color: black;
    background: white;
    border: 1px solid #cccccc;
    padding: 5px;
}

#UpdateTextHint {
    font-size: 20px;
    padding-left: 10px;
    color: black;
    background: none;
}

#order_status {
    font-size: 15px;
    qproperty-alignment: AlignCenter;
    color: black;
    background: none;
}

#order_status_widget {
    border: 3px solid black;
    background: white;
}

/* Специальные стили для подсветки товаров */
.high-sale-item {
    background-color: #2E8B57;  /* Для скидки >15% */
    border: 3px solid black;
}

.high-sale-item #cardText {
    color: white;  /* Белый текст на зеленом фоне */
    background: none;
}

.out-of-stock-item {
    background-color: #87CEEB;  /* Голубой для отсутствия товара */
    border: 3px solid black;
}

.out-of-stock-item #cardText {
    color: black;  /* Черный текст на голубом фоне */
    background: none;
}

.normal-item {
    background-color: white;  /* Обычный товар */
    border: 3px solid black;
}

.normal-item #cardText {
    color: black;
    background: none;
}

/* Стили для цен */
.discounted-price {
    color: black;
    font-weight: bold;
    font-size: 18px;
    background: none;
}

.original-price {
    color: red;
    text-decoration: line-through;
    font-size: 16px;
    background: none;
}

.normal-price {
    color: black;
    font-size: 18px;
    background: none;
}

/* Стили для выпадающих списков */
QComboBox {
    background-color: white;
    color: black;
    border: 1px solid #cccccc;
    padding: 5px;
    font-size: 16px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: none;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: white;
    color: black;
    border: 1px solid #cccccc;
    selection-background-color: #00FA9A;
}

/* Стили для чекбоксов */
QCheckBox {
    color: black;
    background: none;
    font-size: 16px;
}

QCheckBox::indicator {
    width: 15px;
    height: 15px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #cccccc;
    background: white;
}

QCheckBox::indicator:checked {
    border: 1px solid #cccccc;
    background: #00FA9A;
}

/* Стили для таблиц */
QTableWidget {
    background-color: white;
    color: black;
    gridline-color: #cccccc;
    border: 1px solid #cccccc;
}

QTableWidget::item {
    background-color: white;
    color: black;
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #00FA9A;
    color: black;
}

QHeaderView::section {
    background-color: #7FFF00;
    color: black;
    padding: 5px;
    border: 1px solid #cccccc;
    font-weight: bold;
}

/* Стили для сообщений */
QMessageBox {
    background-color: white;
    color: black;
}

QMessageBox QLabel {
    color: black;
    background: none;
}

QMessageBox QPushButton {
    background-color: white;
    color: black;
    border: 1px solid gray;
    padding: 8px 16px;
    font-size: 14px;
    font-family: "Times New Roman";
    min-width: 70px;
}

QMessageBox QPushButton:hover {
    background-color: white;
    color: black;
    border: 1px solid black;
}
"""