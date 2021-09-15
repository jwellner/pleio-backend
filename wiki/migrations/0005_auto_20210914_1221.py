# Generated by Django 3.2.6 on 2021-09-14 12:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0005_alter_scanincident_options'),
        ('wiki', '0004_auto_20210601_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='wiki',
            name='featured_alt',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AddField(
            model_name='wiki',
            name='featured_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='file.filefolder'),
        ),
        migrations.AddField(
            model_name='wiki',
            name='featured_position_y',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='wiki',
            name='featured_video',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='wiki',
            name='featured_video_title',
            field=models.CharField(default='', max_length=256),
        ),
    ]
