from django.urls import path

from .views import ProfileDetailView, ProfileRetrieveAPIView, ProfileUpdateAPIView, ProfileUpdateView, \
    SmsCodeCreateAPIView, SmsCodeCreateView, SmsCodeVerifyAPIView, SmsCodeVerifyView


urlpatterns = [
    path('auth/send_sms/', SmsCodeCreateAPIView.as_view(), name='auth_send_sms'),
    path('auth/verify_sms/', SmsCodeVerifyAPIView.as_view(), name='auth_verify_sms'),
    path('profile/', ProfileRetrieveAPIView.as_view(), name='profile_get'),
    path('profile/update/', ProfileUpdateAPIView.as_view(), name='profile_update'),
    path('web/auth/send_sms/', SmsCodeCreateView.as_view(), name='web_auth_send_sms'),
    path('web/auth/verify_sms/', SmsCodeVerifyView.as_view(), name='web_auth_verify_sms'),
    path('web/profile/', ProfileDetailView.as_view(), name='web_profile_get'),
    path('web/profile/update/', ProfileUpdateView.as_view(), name='web_profile_update'),
]