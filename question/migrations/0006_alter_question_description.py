# Generated by Django 3.2.6 on 2021-10-27 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('question', '0005_auto_20210601_1203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='description',
            field=models.TextField(default=''),
        ),
    ]
