# Generated by Django 3.2.18 on 2023-02-24 08:15

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0085_alter_siteaccessrequest_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='block_reason',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='attachment',
            name='blocked',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='attachment',
            name='last_scan',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
