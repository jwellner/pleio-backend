# Generated by Django 3.1.2 on 2020-11-06 10:56

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_siteaccessrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmembership',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
