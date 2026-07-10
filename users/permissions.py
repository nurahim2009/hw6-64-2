from users.permissions import IsModerator
from rest_framework.permissions import BasePermission

class IsModerator(BasePermission):
    """
    Кастомный permission для модераторов (is_staff=True).
    - Разрешены методы: GET, PUT, PATCH, DELETE.
    - Запрещен метод: POST (создание).
    """

    def has_permission(self, request, view):
        # 1. Проверяем, что пользователь авторизован и является сотрудником (is_staff=True)
        if not (request.user and request.user.is_authenticated and request.user.is_staff):
            return False
        
        # 2. Модератор не может создавать продукты (запрещаем метод POST)
        if request.method == 'POST':
            return False
            
        return True

    def has_object_permission(self, request, view, obj):
        # Модератор может просматривать, изменять и удалять чужие продукты
        return True