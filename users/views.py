import random
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import save_confirmation_code  # Импортируем утилиту


from .utils import get_confirmation_code, delete_confirmation_code



User = get_user_model()

class VerifyCodeView(APIView):
    def post(self, request):
        email = request.data.get('email')
        user_code = request.data.get('code')
        
        # 1. Получаем сохраненный код из оперативной памяти Redis
        saved_code = get_confirmation_code(email)
        
        if not saved_code:
            return Response(
                {"error": "Код не найден или его время жизни (5 минут) истекло."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 2. Проверяем, совпадает ли то, что ввёл юзер, с кодом из Redis
        if saved_code != str(user_code):
            return Response({"error": "Неверный код подтверждения."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 3. Выполняем условие ДЗ: если код верный, сразу стираем его из Redis
        delete_confirmation_code(email)
        
        # 4. Находим пользователя в PostgreSQL по email и активируем его
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                user.is_active = True
                user.save()
        except User.DoesNotExist:
            return Response({"error": "Пользователь с таким email не найден."}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({"message": "Код успешно подтвержден, аккаунт активирован!"}, status=status.HTTP_200_OK)

class SendCodeView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email обязателен"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Генерируем 4- или 6-значный код
        code = random.randint(100000, 999999)
        
        # Сохраняем в Redis на 5 минут
        save_confirmation_code(email, code)
        
        # Здесь идет ваш код отправки email (например, send_mail(...))
        print(f"Код {code} для {email} сохранен в Redis на 5 минут.") # Для отладки
        
        return Response({"message": "Код отправлен на ваш Email."}, status=status.HTTP_200_OK)