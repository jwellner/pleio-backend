# Generated by Django 2.0.9 on 2018-11-20 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20181120_1616'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='featured_image',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='group',
            name='featured_position_y',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='group',
            name='featured_video',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
