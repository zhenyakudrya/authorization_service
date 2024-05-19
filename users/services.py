import os
import random
import string

from twilio.rest import Client


def generate_sms_code():
    """Функция генерации четырехзначных смс кодов."""
    sms_code = random.randint(1000, 9999)
    return sms_code


def send_sms_code(phone_number, sms_code):
    """Функция отправки смс кода через Twilio."""
    account_sid = os.getenv('SMS_CID')  # Twilio account SID
    auth_token = os.getenv('SMS_TOKEN')  # Twilio auth token
    twilio_phone_number = os.getenv('SMS_NUMBER')  # Twilio phone number

    client = Client(account_sid, auth_token)
    client.messages.create(
        body=f'Ваш смс код: {sms_code}',
        from_=twilio_phone_number,
        to=phone_number
    )


def generate_referral_code(length=6):
    """Функция генерации шестизначных кодов реферальной программы из символов и цифр."""
    all_chars = string.ascii_letters + string.digits
    referral_code = ''.join(random.choice(all_chars) for _ in range(length))
    return referral_code