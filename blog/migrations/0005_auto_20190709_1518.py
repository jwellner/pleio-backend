# Generated by Django 2.2.2 on 2019-07-09 15:18

import core.models
import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_auto_20180717_1341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='read_access',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32), blank=True, default=core.models.read_access_default, size=None),
        ),
        migrations.AlterField(
            model_name='blog',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256), blank=True, default=list, size=None),
        ),
        migrations.AlterField(
            model_name='blog',
            name='write_access',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32), blank=True, default=core.models.write_access_default, size=None),
        ),
    ]
