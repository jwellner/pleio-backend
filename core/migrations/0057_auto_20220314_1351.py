# Generated by Django 3.2.6 on 2022-03-14 12:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0056_auto_20220302_1707'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='description',
        ),
        migrations.RemoveField(
            model_name='commentrequest',
            name='description',
        ),
        migrations.RemoveField(
            model_name='group',
            name='description',
        ),
    ]
