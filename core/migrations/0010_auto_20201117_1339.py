# Generated by Django 3.1.2 on 2020-11-17 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_groupmembership_notification_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofilefield',
            name='value',
            field=models.TextField(),
        ),
    ]