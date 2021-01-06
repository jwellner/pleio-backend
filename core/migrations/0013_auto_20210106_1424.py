# Generated by Django 3.1.2 on 2021-01-06 14:24

import core.models.user
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20201221_1114'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='overview_email_interval',
            field=models.CharField(blank=True, choices=[('never', 'Never'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default=core.models.user.get_overview_email_interval_default, max_length=10, null=True),
        ),
    ]