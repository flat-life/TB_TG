# Generated by Django 5.0.1 on 2024-01-22 13:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0013_alter_customer_options_alter_customer_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='placed_at',
        ),
    ]
