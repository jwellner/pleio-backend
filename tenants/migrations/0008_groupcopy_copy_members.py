# Generated by Django 3.2.18 on 2023-03-16 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0007_remove_client_elgg_database'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupcopy',
            name='copy_members',
            field=models.BooleanField(default=False),
        ),
    ]