# Generated by Django 3.2.6 on 2022-03-17 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0012_remove_event_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventattendee',
            name='checked_in_at',
            field=models.DateTimeField(default=None, null=True),
        ),
    ]
