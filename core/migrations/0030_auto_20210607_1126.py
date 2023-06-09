# Generated by Django 3.2.4 on 2021-06-07 11:26

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_group_featured_video_title'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entity',
            options={'ordering': ['published']},
        ),
        migrations.AddField(
            model_name='entity',
            name='published',
            field=models.DateTimeField(null=True, default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='entity',
            name='notifications_created',
            field=models.BooleanField(default=True),
        )
    ]
