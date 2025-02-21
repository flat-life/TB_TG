import datetime
from decimal import Decimal

from django.apps import apps
from parler.models import TranslatableModel

from blog.models import BlogComment, Blog
from core.models import AuditLog, User
from discount.models import BaseDiscount
from shop.models import Customer, Order, Product, Promotion, Collection, OrderItem, Review, Address, Transaction, \
    MainFeature, FeatureKey, FeatureValue
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.db.models.signals import post_save, pre_delete, pre_save
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.files import FileField
from django.db.models.fields import DateTimeField, DateField
import uuid
import inspect

""" 
   ________________________________________________________________________________
  |                   IF WE WANT TO ADD USER INTO DATABASE                         |    
  |                                                                                |
  |  pre_save_signal = Signal(providing_args=["instance", "request"])              |    
  |  post_save_signal = Signal(providing_args=["instance", "created", "request"])  |
  |                                                                                |    
  |  @receiver(post_save_signal, sender=Food)                                      |        
  |  def log_post_save(sender, instance, created, request, **kwargs):              |                
  |      user = request.user if request.user.is_authenticated else None            |        
   ________________________________________________________________________________

"""


def serialize_model_instance(instance):
    serialized_fields = {}

    for field in instance._meta.fields:
        field_value = getattr(instance, field.name)

        if isinstance(field, (DateTimeField, DateField, datetime.date, datetime.datetime)):
            field_value = field_value.isoformat() if field_value else None
        elif isinstance(field, ForeignKey):
            field_value = str(field_value.pk) if field_value else None
        elif isinstance(field, FileField):
            continue
        elif isinstance(field_value, (Decimal, uuid.UUID)):
            field_value = str(field_value)

        serialized_fields[field.name] = field_value

    return serialized_fields


def get_model_changes(old_instance, new_instance):
    changes = {}

    for field in old_instance._meta.fields:
        old_value = getattr(old_instance, field.name)
        new_value = getattr(new_instance, field.name)

        if old_value != new_value:
            if any(isinstance(value, (DateTimeField, Decimal, datetime.date, datetime.datetime, uuid.UUID, DateField))
                   for value in
                   (new_value, old_value)):
                changes[field.name] = {
                    'old_value': str(old_value),
                    'new_value': str(new_value),
                }
            elif isinstance(field, ForeignKey):
                changes[field.name] = {
                    'old_value': old_value.pk if old_value is not None else None,
                    'new_value': new_value.pk if new_value is not None else None,
                }
            else:
                changes[field.name] = {
                    'old_value': old_value,
                    'new_value': new_value,
                }

    return changes


@receiver(pre_save, sender=Customer)
@receiver(pre_save, sender=Review)
@receiver(pre_save, sender=Order)
@receiver(pre_save, sender=Product)
@receiver(pre_save, sender=FeatureKey)
@receiver(pre_save, sender=FeatureValue)
@receiver(pre_save, sender=MainFeature)
@receiver(pre_save, sender=TranslatableModel)
@receiver(pre_save, sender=Promotion)
@receiver(pre_save, sender=BaseDiscount)
@receiver(pre_save, sender=Collection)
@receiver(pre_save, sender=Address)
@receiver(pre_save, sender=OrderItem)
@receiver(pre_save, sender=Transaction)
@receiver(pre_save, sender=Blog)
@receiver(pre_save, sender=BlogComment)
def log_create_update(sender, instance, **kwargs):
    model_name = sender.__name__  # just for fun :-|
    try:
        old_instance = sender._default_manager.get(pk=instance.pk)  #:-)
        # print('old_instance', old_instance)
    except sender.DoesNotExist:
        action = 'CREATE'
        old_value = None
        changes = serialize_model_instance(instance)
    else:
        action = 'UPDATE'
        old_value = serialize_model_instance(old_instance)
        changes = get_model_changes(old_instance, instance)
        # print('old_value', old_value)
        # print('changes', changes)

    table_name = sender._meta.db_table
    row_id = instance.id
    """                                                                                               """"""
    |                                                                                                   |        
    |        https://stackoverflow.com/questions/4721771/get-current-user-log-in-signal-in-django       |
    |                                                                                                   |
    """                                                                                               """"""
    # refrence is up here
    request = None
    for frame_record in inspect.stack():
        if frame_record[3] == 'get_response':
            request = frame_record[0].f_locals['request']
            """https://docs.python.org/3/library/inspect.html"""
            """https://www.geeksforgeeks.org/inspect-module-in-python/"""
            break

    if request:
        user = request.user
        if not isinstance(user, User):
            user = None
    else:
        user = None

    AuditLog.objects.create(
        user=user,
        action=action,
        table_name=table_name,
        row_id=row_id,
        old_value=old_value,
        changes=changes,
    )


def models_with_translations():
    models_with_translation = []
    for model in apps.get_models():
        if 'translation' in model.__name__.lower():
            models_with_translation.append(model)
    return models_with_translation


def create_signal_recivers_for_models_with_translation():
    models_with_translation = models_with_translations()
    print(models_with_translation)
    for model in models_with_translation:
        pre_save.connect(log_create_update, sender=model)


create_signal_recivers_for_models_with_translation()
