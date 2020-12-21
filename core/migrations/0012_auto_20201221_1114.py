# Generated by Django 3.1.2 on 2020-12-21 11:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0011_auto_20201127_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupinvitation',
            name='email',
            field=models.EmailField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='groupinvitation',
            name='invited_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invitation', to=settings.AUTH_USER_MODEL),
        ),
    ]
