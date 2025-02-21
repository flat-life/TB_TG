import inspect
from time import sleep

from django.conf import settings
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from core.models import User
from .models import Customer, Order, Transaction, OrderItem, CartItem, Cart


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_for_new_user(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)


@receiver(post_save, sender=Order)
def create_transaction_for_new_order(sender, instance: Order, created, **kwargs):
    order = instance
    if created:
        sleep(0.5)
        total_price = 0
        customer = instance.customer
        phone_number = customer.user.phone_number
        receipt_number = None
        Transaction.objects.create(order=order, customer=customer, total_price=total_price,
                                   receipt_number=receipt_number, phone_number=phone_number)
    else:
        transaction = Transaction.objects.get(order=order)
        total_price = order.get_total_price()
        transaction.total_price = total_price
        transaction.save()


@receiver(post_save, sender=OrderItem)
def update_total_sales_of_transaciton(sender, instance, created, **kwargs):
    order_item: OrderItem = instance
    order = order_item.order
    transaction = Transaction.objects.get(order=order)
    total_price = order.get_total_price()
    transaction.total_price = total_price
    transaction.save()


User = get_user_model()

from django.http import HttpRequest
from rest_framework.request import Request as DRFRequest

@receiver(post_save, sender=CartItem)
def update_cart_customer(sender, instance, created, **kwargs):
    request = None
    # Iterate through all frames in the stack
    for frame_record in inspect.stack():
        frame = frame_record.frame
        frame_locals = frame.f_locals

        # Check if 'request' exists in the frame's locals
        if 'request' in frame_locals:

            candidate = frame_locals['request']
            # Verify the candidate is a request object
            if isinstance(candidate, (HttpRequest, DRFRequest)):
                request = candidate
                break  # Exit loop once request is found
    print('request',request)
    # Proceed if request was found
    if request:
        user = request.user
        # Ensure user is a valid User instance
        if not isinstance(user, User):
            user = None
    else:
        user = None

    # Update cart customer if user is valid
    if user:
        cart = instance.cart
        # Assuming Customer is linked to User via a one-to-one relationship
        cart.customer = user.customer
        cart.save()
