# Generated by Django 3.2.6 on 2022-02-16 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_auto_20220203_1553'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
