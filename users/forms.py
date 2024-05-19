import re

from django import forms

from rest_framework.generics import get_object_or_404

from users.models import User


class SendSmsForm(forms.Form):
    """Форма для авторизации: отправка смс кода."""

    phone_number = forms.CharField(max_length=15)

    def clean_phone_number(self):
        """Метод валидации номера телефона."""
        cleaned_data = self.cleaned_data['phone_number']
        pattern = r'\+7\d{10}$'
        if not re.match(pattern, cleaned_data):
            raise forms.ValidationError("Номер телефона должен начинаться с +7 и иметь 11 цифр")
        return cleaned_data


class PhoneSmsForm(forms.Form):
    """Форма для авторизации: проверка смс кода."""

    phone_number = forms.CharField(max_length=12)
    sms_code = forms.IntegerField(required=False)

    def clean_phone_number(self):
        """Метод валидации номера телефона."""
        cleaned_data = self.cleaned_data['phone_number']
        pattern = r'\+7\d{10}$'
        if not re.match(pattern, cleaned_data):
            raise forms.ValidationError("Номер телефона должен начинаться с +7 и иметь 11 цифр")
        return cleaned_data

    def clean_sms_code(self):
        """Метод валидации смс кода."""
        cleaned_data = str(self.cleaned_data['sms_code'])
        if len(cleaned_data) != 4:
            raise forms.ValidationError("Код должен состоять из 4 цифр")
        return cleaned_data


class ProfileForm(forms.ModelForm):
    """Форма профиля пользователя."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number',
                  'my_referral_code', 'referral_points', 'inviter_referral_code',)


class ProfileUpdateForm(forms.ModelForm):
    """Форма обновления профиля пользователя."""

    def clean_inviter_referral_code(self):
        """Метод валидации реферального кода пригласителя."""
        cleaned_data = self.cleaned_data['inviter_referral_code']

        if cleaned_data is not None:
            if self.instance.inviter_referral_code is not None:
                raise forms.ValidationError('Реферальный код уже активирован')
            elif not User.objects.filter(my_referral_code=cleaned_data).exists():
                raise forms.ValidationError('Введенный вами код не существует')
            elif cleaned_data == self.instance.my_referral_code:
                raise forms.ValidationError('Вы не можете использовать собственный реферальный код')
            elif User.objects.filter(my_referral_code=cleaned_data).exists():
                if self.instance.my_referral_code == User.objects.get(
                        my_referral_code=cleaned_data).inviter_referral_code:
                    raise forms.ValidationError('Вы не можете использовать код пользователя, которого пригласили сами')
        else:
            cleaned_data = self.instance.inviter_referral_code

        return cleaned_data

    def save(self, commit=True):
        """Метод начисления реферальных баллов."""
        inviter_referral_code_before_update = User.objects.get(id=self.instance.id).inviter_referral_code
        instance = super().save(commit=False)
        cleaned_data = self.cleaned_data['inviter_referral_code']

        if cleaned_data is not None and inviter_referral_code_before_update is None:
            instance.inviter_referral_code = cleaned_data
            instance.referral_points += 100  # приглашенному
            inviter = get_object_or_404(User.objects.all(), my_referral_code=instance.inviter_referral_code)
            inviter.referral_points += 200  # пригласившему
            inviter.save()

        if commit:
            instance.save()

        return instance

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'inviter_referral_code',)