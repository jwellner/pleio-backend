# Generated by Django 3.1.6 on 2021-02-23 16:56

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('flow', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flowid',
            name='flow_id',
            field=models.IntegerField(editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='flowid',
            name='object_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
