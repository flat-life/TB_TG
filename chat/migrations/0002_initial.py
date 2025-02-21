# Generated by Django 5.0.1 on 2025-02-09 11:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('chat', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='receiver_conversation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='receiver_conversation', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conversation',
            name='sender_conversation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sender_conversation', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='conversation_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.conversation'),
        ),
        migrations.AddField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='message_sender', to=settings.AUTH_USER_MODEL),
        ),
    ]
