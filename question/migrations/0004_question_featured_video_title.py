# Generated by Django 3.2.5 on 2021-07-14 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('question', '0003_auto_20210124_0739'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='featured_video_title',
            field=models.CharField(default='', max_length=256),
        ),
    ]
