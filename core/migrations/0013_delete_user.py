# Generated by Django 2.2.8 on 2020-02-13 14:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_userprofile_overview_email_tags'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
    ]
