import requests
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# Сюда вставьте ваши данные из Google Console (лучше вынести в settings.py / .env)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

class GoogleLoginView(APIView):
    """
    Эндпоинт, возвращающий URL для перенаправления пользователя на авторизацию Google.
    """
    def get(self, request):
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={GOOGLE_CLIENT_ID}"
            f"&redirect_uri={GOOGLE_REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
            f"&access_type=offline"
        )
        return Response({"auth_url": auth_url}, status=status.HTTP_200_OK)


class GoogleCallbackView(APIView):
    """
    Эндпоинт, куда Google отправляет пользователя с `code` в параметрах URL.
    """
    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({"error": "Code not provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Обмениваем код (code) на Access Token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI,
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        access_token = token_json.get('access_token')
        if not access_token:
            return Response({"error": "Failed to obtain access token", "details": token_json}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Получаем данные профиля пользователя с помощью Access Token
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
        user_data = user_info_response.json()

        email = user_data.get('email')
        given_name = user_data.get('given_name', '')  # Имя
        family_name = user_data.get('family_name', '') # Фамилия

        if not email:
            return Response({"error": "Email not provided by Google"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Находим пользователя или создаем нового
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0], # Создаем базовый username из email
                'first_name': given_name,
                'last_name': family_name,
                'is_active': True,
                'registration_source': 'google'
            }
        )

        # Если пользователь уже существовал, но входит через Google:
        if not created:
            user.is_active = True
            # На случай, если имя/фамилия изменились или не были заполнены:
            if given_name: user.first_name = given_name
            if family_name: user.last_name = family_name

        # Обновляем дату последнего входа (требование ДЗ)
        user.last_login = timezone.now()
        user.save()

        # 4. Генерируем JWT-токен вашей системы для аутентифицированного пользователя
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "Успешный вход через Google",
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "registration_source": user.registration_source
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)