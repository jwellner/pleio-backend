# Generated by Django 3.2.5 on 2021-07-14 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_blog_featured_alt'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='featured_video_title',
            field=models.CharField(default='', max_length=256),
        ),
    ]
