# Generated by Django 2.2.6 on 2019-10-15 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20190924_1410'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_delete_requested',
            field=models.BooleanField(default=False),
        ),
    ]
