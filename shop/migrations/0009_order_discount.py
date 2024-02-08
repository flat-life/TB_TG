# Generated by Django 5.0.1 on 2024-02-07 08:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discount', '0002_delete_usagecount'),
        ('shop', '0008_alter_cart_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='discount',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='discount.basediscount', verbose_name='Discount'),
        ),
    ]
