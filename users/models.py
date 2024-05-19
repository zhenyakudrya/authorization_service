from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Пользователь."""

    my_referral_code = models.CharField(max_length=6, null=True, blank=True, verbose_name='собственный реф. код')
    inviter_referral_code = models.CharField(max_length=6, null=True, blank=True, verbose_name='реф. код пригласителя')
    referral_points = models.PositiveSmallIntegerField(default=0, verbose_name='реф. баллы')

    username: None = None
    password = None
    phone_number = models.CharField(max_length=12, unique=True, verbose_name='номер телефона')

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        """Метод возвращает строковое представление объекта."""
        return self.phone_number


class AuthCode(models.Model):
    """Код авторизации."""

    phone_number = models.CharField(max_length=15, unique=True, verbose_name='номер телефона')
    sms_code = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='смс код для авторизации')
    sms_code_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='время отправки смс кода')

    def __str__(self):
        """Метод возвращает строковое представление объекта."""
        return f'{self.phone_number}:{self.sms_code}'

    def is_sms_code_valid(self):
        """Метод проверки актуальности смс кода: не старше 5 минут."""
        if self.sms_code_sent_at:
            time_difference = timezone.now() - self.sms_code_sent_at
            return time_difference.total_seconds() <= 300  # 300 секунд (5 минут)
        return False
