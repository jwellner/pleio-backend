# Generated by Django 3.2.6 on 2022-01-31 16:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_auto_20220119_1317'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userprofilefield',
            unique_together={('user_profile', 'profile_field')},
        ),
    ]
