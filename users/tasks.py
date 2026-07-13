import logging
from datetime import datetime, timedelta
from celery import shared_task
from celery.schedules import crontab
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)

# =====================================================================
# 1. ЗАДАЧА ДЛЯ ЗАПУСКА ЧЕРЕЗ .delay()
# Пример: Асинхронное удаление старых логов или неактивных черновиков
# =====================================================================
@shared_task
def delete_old_temporary_data():
    """
    Имитация очистки временных данных.
    Запускается вручную из view при определенных действиях пользователя через .delay()
    """
    logger.info("Начало очистки временных данных...")
    # Здесь могла бы быть логика: TemporaryModel.objects.filter(created_at__lt=...).delete()
    logger.info("Временные данные успешно удалены.")
    return "Очистка завершена"


# =====================================================================
# 2. ЗАДАЧА ПО РАСПИСАНИЮ ЧЕРЕЗ crontab (Celery Beat)
# Пример: Каждую ночь в 03:00 деактивировать пользователей, 
# которые не заходили в систему более 6 месяцев.
# =====================================================================
@shared_task
def deactivate_inactive_users():
    """
    Периодическая задача для отключения неактивных аккаунтов.
    """
    six_months_ago = datetime.now() - timedelta(days=180)
    
    # Ищем пользователей, которые не заходили последние 6 месяцев и еще активны
    inactive_users = User.objects.filter(last_login__lt=six_months_ago, is_active=True)
    count = inactive_users.count()
    
    # Деактивируем их
    inactive_users.update(is_active=False)
    
    logger.info(f"Супервизор Celery: Деактивировано неактивных пользователей: {count}")
    return f"Деактивировано: {count}"


# =====================================================================
# 3. ЗАДАЧА С ИСПОЛЬЗОВАНИЕМ SMTP (Отправка Email)
# Пример: Отправка приветственного письма после успешной регистрации
# =====================================================================
@shared_task
def send_welcome_email(user_email, username):
    """
    Фоновая отправка email через SMTP-сервер, чтобы не тормозить HTTP-ответ.
    """
    subject = "Добро пожаловать в нашу систему!"
    message = f"Здравствуйте, {username}!\n\nСпасибо за регистрацию на нашем портале."
    from_email = settings.DEFAULT_FROM_EMAIL
    
    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[user_email],
        fail_silently=False,
    )
    logger.info(f"Приветственное письмо успешно отправлено на {user_email}")
    return f"Email sent to {user_email}"