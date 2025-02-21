import uuid
from datetime import timedelta

import redis
from django.conf import settings
from django.utils import timezone
from rest_framework import status
import pytest
from model_bakery import baker

from discount.models import BaseDiscount
from shop.models import Product, CartItem


@pytest.mark.django_db
class TestAuth:

    def test_create_user_return_201(self, api_client):
        response = api_client.post(
            '/api-v1/users/',
            {
                "phone_number": "09887776655",
                "email": "yosofasadi22@gmail.com",
                "password": "FiFiFoopatech"
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        response = api_client.post(
            '/api-v1/users/',
            {
                "phone_number": "09887776655",
                "email": "yosofasaddi22@gmail.com",
                "password": "FiFiFodopatech"
            },
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_otp(self, api_client):
        response = api_client.post(
            '/api-v1/users/',
            {
                "phone_number": "09887776655",
                "email": "yosofasadi22@gmail.com",
                "password": "FiFiFoopatech"
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        response = api_client.post(
            '/api-v1/login-otp/',
            {
                "email": "yosofasadi22@gmail.com",
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_verify_otp(self, api_client):
        response = api_client.post(
            '/api-v1/users/',
            {
                "phone_number": "09887776655",
                "email": "yosofasadi22@gmail.com",
                "password": "FiFiFoopatech"
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        response = api_client.post(
            '/api-v1/login-otp/',
            {
                "email": "yosofasadi22@gmail.com",
            },
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        email = 'yosofasadi22@gmail.com'
        otp_key = f'otp:{email}'
        stored_otp = redis.StrictRedis(host=settings.REDIS_HOST_OTP, port=settings.REDIS_PORT,
                                       db=settings.REDIS_DB).get(otp_key)
        stored_otp = str(stored_otp.decode('utf_8'))
        response = api_client.post(
            '/api-v1/verify-otp/',
            {
                "email": "yosofasadi22@gmail.com",
                "otp": f"{str(stored_otp)}"
            },
            format='json'
        )
        print(stored_otp)
        print(response.data)
        assert response.status_code == status.HTTP_200_OK
