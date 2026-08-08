styles_sheet = """
/* Базовые настройки */
QWidget {
    background-color: #FFFFFF;
    font-family: "Times New Roman";
    color: black;
}

/* Общие свойства текста */
#Title, #FIO, #cardText, #UpdateTextHint,
#sale_text, #text_logo, #original_price,
#discounted_price, #normal_price, #stock_count,
#order_article, #order_text, #delivery_title, #delivery_date {
    background: none;
}

#cardText, #search_edit, #UpdateTextEdit,
#UpdateTextHint, #stock_count, #order_article, #delivery_date {
    font-size: 20px;
}

#original_price, #discounted_price, #normal_price,
#order_text, #small_button {
    font-size: 18px;
}

#Title, #text_logo, #discounted_price, #normal_price,
#order_article, #delivery_title, #delivery_date {
    font-weight: bold;
}

#Title, #sale_text {
    qproperty-alignment: AlignCenter;
}

#Title {
    font-size: 60px;
}

#FIO {
    font-size: 30px;
    qproperty-alignment: AlignRight;
    padding-right: 10px;
}

#text_logo {
    font-size: 28px;
}

#sale_text {
    font-size: 22px;
}

#UpdateTextHint {
    padding-left: 10px;
}

/* Поля ввода */
#LogInEdit, #UpdateTextEdit {
    background: white;
    border: 1px solid #cccccc;
}

#LogInEdit {
    font-size: 30px;
    padding: 10px;
}

#UpdateTextEdit {
    padding: 5px;
}

#search_edit {
    padding: 10px;
    border: 1px solid black;
    background: white;
}

/* Кнопки */
#button, #table_button, #small_button {
    background: #00FA9A;
    border: 1px solid black;
}

#button {
    font-size: 40px;
    padding: 10px;
}

#button:hover {
    font-weight: bold;
    border-width: 2px;
}

#table_button {
    padding: 4px 8px;
}

#small_button {
    padding: 6px 12px;
}

/* Шапка */
#back_header_button {
    font-size: 30px;
    background: #7FFF00;
    border: none;
    padding: 20px;
}

#back_header_button:hover {
    font-weight: bold;
}

#header_widget {
    background: #7FFF00;
    border: 1px solid black;
}

#header_widget QWidget {
    background: none;
    border: none;
}

/* Карточки товаров */
#item_card {
    border: 3px solid black;
    background: white;
}

#sale_widget, #update_button {
    border: 1px solid black;
    background: white;
}

#product_image_preview {
    border: 1px solid gray;
    background: white;
}

#item_card[state="high_discount"],
#item_card[state="high_discount"] #update_button,
#item_card[state="high_discount"] #product_information {
    background-color: #2E8B57;
}

#item_card[state="out_of_stock"],
#item_card[state="out_of_stock"] #update_button,
#item_card[state="out_of_stock"] #product_information {
    background-color: #87CEEB;
}

#item_card[state="high_discount"] #cardText,
#item_card[state="high_discount"] #stock_count {
    color: white;
}

#product_picture {
    background: white;
    border: 1px solid #cccccc;
}

#original_price {
    color: red;
    text-decoration: line-through;
}

/* Карточки заказов */
#delivery_box {
    min-width: 150px;
    max-width: 150px;
    border: 2px solid black;
    background: white;
}

#delivery_title {
    font-size: 16px;
}

#order_item_name, #order_item_details, #empty_text,
QMessageBox QPushButton {
    font-size: 14px;
}

#order_item_details, #empty_text {
    color: gray;
}

/* Выпадающие списки */
QComboBox {
    background-color: white;
    color: black;
    border: 1px solid #cccccc;
    padding: 5px;
    font-size: 16px;
}

QComboBox::drop-down, QComboBox::down-arrow {
    border: none;
}

QComboBox::down-arrow {
    image: none;
}

QComboBox QAbstractItemView {
    background-color: white;
    color: black;
    border: 1px solid #cccccc;
    selection-background-color: #00FA9A;
}

/* Таблицы */
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

/* Информационные окна */
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
    font-family: "Times New Roman";
    min-width: 70px;
}

QMessageBox QPushButton:hover {
    border-color: black;
}
"""