# Generated by Django 3.2.13 on 2022-06-01 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0063_auto_20220401_1128'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='schedule_archive_after',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='entity',
            name='schedule_delete_after',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
