# Generated by Django 3.2.18 on 2023-05-08 08:29

import core.models.group
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0090_auto_20230406_1457'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='widget_repository',
            field=models.JSONField(default=core.models.group._default_widget_repository, null=True),
        ),
    ]