# Generated by Django 3.2.18 on 2023-04-11 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0027_add_range_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='range_cycle',
            field=models.IntegerField(default=1),
        ),
    ]
