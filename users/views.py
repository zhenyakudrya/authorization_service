from django.contrib.auth import login
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, UpdateView

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import AccessToken

from twilio.base.exceptions import TwilioRestException

from users.models import AuthCode, User

from .forms import PhoneSmsForm, ProfileForm, ProfileUpdateForm
from .serializers import PhoneSmsSerializer, ProfileSerializer
from .services import generate_referral_code, generate_sms_code, send_sms_code


class SmsCodeCreateAPIView(APIView):
    """Контроллер для авторизации: отправка смс кода."""

    @staticmethod
    def post(request):
        """Метод обрабатывает POST запрос для отправки смс кода."""
        phone_number = request.data.get('phone_number')
        serializer = PhoneSmsSerializer(data={'phone_number': phone_number})
        if serializer.is_valid():
            try:
                sms_code = generate_sms_code()
                send_sms_code(phone_number, sms_code)
                auth_code, created = AuthCode.objects.get_or_create(phone_number=phone_number)
                auth_code.sms_code = sms_code
                auth_code.sms_code_sent_at = timezone.now()
                auth_code.save()
                return Response({'message': 'Смс код отправлен успешно'}, status=status.HTTP_200_OK)
            except TwilioRestException:
                return Response({'message': 'Ошибка отправки смс кода'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=400)


class SmsCodeVerifyAPIView(APIView):
    """Контроллер для авторизации: проверка смс кода."""

    @staticmethod
    def post(request):
        """Метод обрабатывает POST запрос для проверки смс кода."""
        phone_number = request.data.get('phone_number')
        sms_code = request.data.get('sms_code')
        serializer = PhoneSmsSerializer(data={'phone_number': phone_number, 'sms_code': sms_code})
        if serializer.is_valid():
            try:
                auth_code = AuthCode.objects.get(phone_number=phone_number, sms_code=sms_code)

                if not auth_code.is_sms_code_valid():
                    return Response({'message': 'Срок действия смс кода вышел'}, status=status.HTTP_400_BAD_REQUEST)

                user, created = User.objects.get_or_create(phone_number=phone_number)
                if created:
                    user.my_referral_code = generate_referral_code()
                    user.save()

                access_token = str(AccessToken.for_user(user))

                return Response({'message': 'Авторизация прошла успешно', 'access_token': access_token})
            except AuthCode.DoesNotExist:
                return Response({'message': 'Неверный номер телефона или смс код'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=400)


class ProfileRetrieveAPIView(generics.RetrieveAPIView):
    """Контроллер, который позволяет пользователям просматривать свой собственный профиль."""

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Метод возвращает экземпляр пользователя, который в данный момент авторизован."""
        return self.request.user


class ProfileUpdateAPIView(generics.UpdateAPIView):
    """Контроллер, который позволяет пользователям обновлять свой собственный профиль."""

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Метод возвращает экземпляр пользователя, который в данный момент авторизован."""
        return self.request.user


class SmsCodeCreateView(FormView):
    """Контроллер веб-теста для авторизации: отправка смс кода."""

    form_class = PhoneSmsForm
    template_name = 'users/auth_send_sms.html'
    success_url = reverse_lazy('users:web_auth_verify_sms')

    def form_valid(self, form):
        """Метод обрабатывает валидную форму для отправки смс кода."""
        phone_number = form.cleaned_data['phone_number']

        try:
            sms_code = generate_sms_code()
            send_sms_code(phone_number, sms_code)
            auth_code, create = AuthCode.objects.get_or_create(phone_number=phone_number)
            auth_code.sms_code = sms_code
            auth_code.sms_code_sent_at = timezone.now()
            auth_code.save()
        except TwilioRestException:
            return render(self.request, self.template_name, {'error_message': 'Ошибка отправки sms кода'})

        return super().form_valid(form)


class SmsCodeVerifyView(FormView):
    """Контроллер веб-теста для авторизации: проверка смс кода."""

    form_class = PhoneSmsForm
    template_name = 'users/auth_verify_sms.html'
    success_url = reverse_lazy('users:web_profile_get')

    def form_valid(self, form):
        """Метод обрабатывает валидную форму для проверки смс кода."""
        phone_number = form.cleaned_data['phone_number']
        sms_code = form.cleaned_data['sms_code']
        try:
            auth_code = AuthCode.objects.get(phone_number=phone_number, sms_code=sms_code)

            if not auth_code.is_sms_code_valid():
                return render(self.request, self.template_name, {'error_message': 'Срок действия смс кода вышел'})

            user, created = User.objects.get_or_create(phone_number=phone_number)
            if created:
                user.my_referral_code = generate_referral_code()
                user.save()
            login(self.request, user)
        except AuthCode.DoesNotExist:
            return render(self.request, self.template_name, {'error_message': 'Неверный номер телефона или смс код'})

        return super().form_valid(form)


class ProfileDetailView(DetailView):
    """Контроллер веб-теста, который позволяет пользователям просматривать свой собственный профиль."""

    model = User
    form_class = ProfileForm
    template_name = 'users/user_detail.html'

    def get_object(self, *args, **kwargs):
        """Метод возвращает экземпляр пользователя, который в данный момент авторизован."""
        return self.request.user

    def get_context_data(self, **kwargs):
        """Метод получения списка номеров телефонов рефералов."""
        context_data = super().get_context_data(**kwargs)
        referrals = User.objects.filter(inviter_referral_code=self.request.user.my_referral_code)
        context_data['referrals'] = [referral.phone_number for referral in referrals]  # только номера телефонов
        return context_data


class ProfileUpdateView(UpdateView):
    """Контроллер веб-теста, который позволяет пользователям изменять свой собственный профиль."""

    model = User
    form_class = ProfileUpdateForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:web_profile_get')

    def get_object(self, *args, **kwargs):
        """Метод возвращает экземпляр пользователя, который в данный момент авторизован."""
        return self.request.user