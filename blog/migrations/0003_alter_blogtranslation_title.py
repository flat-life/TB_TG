# Generated by Django 5.0.1 on 2024-02-16 01:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_alter_blogcomment_blog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogtranslation',
            name='title',
            field=models.CharField(max_length=255, unique=True, verbose_name='Title'),
        ),
    ]
