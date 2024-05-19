import re

from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import ValidationError

from users.models import User


class PhoneSmsSerializer(serializers.Serializer):
    """Сериализатор для номера телефона и смс кода."""

    phone_number = serializers.CharField(max_length=12)
    sms_code = serializers.IntegerField(required=False)

    @staticmethod
    def validate_phone_number(value):
        """Метод валидации номера телефона."""
        pattern = r'\+7\d{10}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("Номер телефона должен начинаться с +7 и иметь 11 цифр")
        return value

    @staticmethod
    def validate_sms_code(value):
        """Метод валидации смс кода."""
        if len(str(value)) != 4:
            raise serializers.ValidationError("Код должен состоять из 4 цифр")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Пользователь."""

    class Meta:
        model = User
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля Пользователя."""

    referrals = serializers.SerializerMethodField(read_only=True)  # список рефералов

    @staticmethod
    def get_referrals(instance):
        """Метод получения списка номеров телефонов рефералов."""
        refs = User.objects.filter(inviter_referral_code=instance.my_referral_code).values_list(
            'phone_number', flat=True)
        return refs

    def validate(self, attrs):
        """Метод валидации поля inviter_referral_code."""
        inviter_referral_code = attrs.get('inviter_referral_code')

        if inviter_referral_code is not None:
            if self.instance.inviter_referral_code is not None and \
                    inviter_referral_code != self.instance.inviter_referral_code:
                raise ValidationError('Реферальный код уже активирован')
            elif not User.objects.filter(my_referral_code=inviter_referral_code).exists():
                raise ValidationError('Введенный вами код не существует')
            elif inviter_referral_code == self.instance.my_referral_code:
                raise ValidationError('Вы не можете использовать собственный реферальный код')
            elif User.objects.filter(my_referral_code=inviter_referral_code).exists():
                if self.instance.my_referral_code == User.objects.get(
                        my_referral_code=inviter_referral_code).inviter_referral_code:
                    raise ValidationError('Вы не можете использовать код пользователя, которого пригласили сами')
        else:
            attrs['inviter_referral_code'] = self.instance.inviter_referral_code

        return attrs

    def update(self, instance, validated_data):
        """Метод начисления реферальных баллов."""
        inviter_referral_code_before_update = instance.inviter_referral_code
        super().update(instance, validated_data)
        inviter_referral_code = validated_data.get('inviter_referral_code', None)

        if inviter_referral_code is not None and inviter_referral_code_before_update is None:

            instance.inviter_referral_code = inviter_referral_code
            instance.referral_points += 100  # приглашенному
            instance.save()
            inviter = get_object_or_404(User.objects.all(), my_referral_code=instance.inviter_referral_code)
            inviter.referral_points += 200  # пригласившему
            inviter.save()

        return instance

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number',
                  'my_referral_code', 'referrals', 'referral_points', 'inviter_referral_code']
        read_only_fields = ('phone_number', 'my_referral_code')