# Generated by Django 3.1.5 on 2021-02-08 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20210125_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='setting',
            name='key',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]