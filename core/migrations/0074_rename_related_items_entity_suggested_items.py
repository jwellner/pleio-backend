# Generated by Django 3.2.14 on 2022-08-29 10:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0073_avatarexport_updated_at'),
    ]

    operations = [
        migrations.RenameField(
            model_name='entity',
            old_name='related_items',
            new_name='suggested_items',
        ),
    ]