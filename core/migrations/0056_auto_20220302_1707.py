# Generated by Django 3.2.6 on 2022-03-02 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0055_delete_draftbackup'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='required_fields_message',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='groupprofilefieldsetting',
            name='is_required',
            field=models.BooleanField(default=False),
        ),
    ]
