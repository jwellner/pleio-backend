# Generated by Django 3.2.16 on 2023-02-08 09:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0007_remove_client_elgg_database'),
        ('control', '0003_accesslog'),
    ]

    operations = [
        migrations.AddField(
            model_name='accesslog',
            name='site',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='tenants.client'),
        ),
    ]
