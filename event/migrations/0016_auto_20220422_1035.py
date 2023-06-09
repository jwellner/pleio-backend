# Generated by Django 3.2.6 on 2022-04-22 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0015_auto_20220408_1202'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='qr_access',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='eventattendee',
            name='code',
            field=models.CharField(blank=True, max_length=36, null=True),
        ),
    ]
