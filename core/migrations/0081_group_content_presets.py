# Generated by Django 3.2.16 on 2022-12-01 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0080_profileset'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='content_presets',
            field=models.JSONField(default=dict),
        ),
    ]
