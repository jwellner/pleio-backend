# Generated by Django 2.2.12 on 2020-05-28 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_userprofile_overview_email_last_received'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='overview_email_interval',
            field=models.CharField(blank=True, choices=[('never', 'Never'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default=None, max_length=10, null=True),
        ),
    ]