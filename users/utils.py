import redis
from django.conf import settings

# Инициализируем клиент Redis
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True  # Чтобы из Redis возвращались строки (str), а не байты (bytes)
)

def save_confirmation_code(email, code):
    """
    Сохраняет код подтверждения для email в Redis на 5 минут (300 секунд).
    """
    key = f"confirm:{email}"
    # setex записывает ключ и сразу выставляет ему TTL (время жизни)
    redis_client.setex(name=key, time=300, value=str(code))

def get_confirmation_code(email):
    """
    Получает код из Redis для конкретного email.
    Если кода нет или время жизни истекло, вернет None.
    """
    key = f"confirm:{email}"
    return redis_client.get(key)

def delete_confirmation_code(email):
    """
    Удаляет код из Redis (используется сразу после успешной проверки).
    """
    key = f"confirm:{email}"
    redis_client.delete(key)