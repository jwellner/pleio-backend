# Generated by Django 2.0 on 2018-07-18 15:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20180718_1508'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='content_id',
            new_name='object_id',
        ),
    ]
