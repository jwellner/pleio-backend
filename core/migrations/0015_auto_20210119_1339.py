# Generated by Django 3.1.5 on 2021-01-19 13:39

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_group_featured_alt'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profilefield',
            options={'ordering': ['created_at', 'id']},
        ),
        migrations.AddField(
            model_name='profilefield',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
