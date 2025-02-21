import logging
import random
import redis
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

security_logger = logging.getLogger('security_logger')


class Authentication:

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    @staticmethod
    def send_otp_email(to_email, otp_key):
        otp = Authentication.generate_otp()

        # Store OTP in Redis with a key
        redis_connection = redis.StrictRedis(host=settings.REDIS_HOST_OTP, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        redis_connection.set(otp_key, otp, ex=settings.OTP_EXPIRY_SECONDS)

        otp_expiry = timezone.now() + timezone.timedelta(seconds=settings.OTP_EXPIRY_SECONDS)

        subject = 'Your verification Code'
        message = f'Your code is: {otp}'
        print(f'code : {otp}')

        try:
            email_from = 'djmailyosof@gmail.com'
            recipient_list = [to_email, ]
            send_mail(subject, message, email_from, recipient_list, auth_user=email_from,
                      auth_password=settings.EMAIL_HOST_PASSWORD)
            security_logger.info(f'otp send to user {to_email} : {otp}')
            return otp, otp_expiry
        except Exception as e:
            raise ConnectionError
