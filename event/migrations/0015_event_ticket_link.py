# Generated by Django 3.2.6 on 2022-04-21 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0014_auto_20220421_1118'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='ticket_link',
            field=models.TextField(default=''),
        ),
    ]
