# Generated by Django 3.2.18 on 2023-03-16 13:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0087_auto_20230316_1419'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupmembership',
            name='notification_mode',
        ),
    ]
