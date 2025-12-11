class Storage:
    user_login_pk: str = None
    user_role: str = None

    # Список действий для каждой роли
    roles_actions = {
        "Администратор": ["Поиск", "Сортировка", "Фильтрация", "Заказы"],
        "Менеджер": ["Поиск", "Сортировка", "Фильтрация", "Заказы"],
        "Авторизированный клиент": [],
        "Гость": []
    }

    # id товара, с которым идет работа (Редактирование)
    current_item_id: str = None

    # Id выбранного для редактирования заказа
    current_order_id: str = None

    @staticmethod
    def set_item_id(new_id):
        Storage.current_item_id = new_id

    @staticmethod
    def get_item_id(): 
        return Storage.current_item_id if Storage.current_item_id else None

    @staticmethod
    def get_roles_action():
        if Storage.user_role and Storage.user_role in Storage.roles_actions:
            return Storage.roles_actions[Storage.user_role]
        return []

    @staticmethod
    def set_user_login(new_login: str):
        """
        Метод для установки логина активного пользователя
        :param new_login: Новый логин активного пользователя
        :return: none
        """
        Storage.user_login_pk = new_login

    @staticmethod
    def get_user_login() -> str: 
        return Storage.user_login_pk if Storage.user_login_pk else "Гость"

    @staticmethod
    def set_user_role(new_role: str):
        """
        Метод для установки роли активного пользователя
        :param new_role: Роль активного пользователя
        :return: none
        """
        Storage.user_role = new_role

    @staticmethod
    def get_user_role() -> str: 
        return Storage.user_role if Storage.user_role else "Гость"
    
    @staticmethod
    def set_order_id(new_id):
        Storage.current_order_id = new_id
        print(f"Storage: установлен order_id = {new_id}")

    @staticmethod
    def get_order_id(): 
        return Storage.current_order_id if Storage.current_order_id else None

    @staticmethod
    def clear_all():
        """Очищает все временные данные"""
        Storage.user_login_pk = None
        Storage.user_role = None
        Storage.current_item_id = None
        Storage.current_order_id = None
        print("Storage: все данные очищены")