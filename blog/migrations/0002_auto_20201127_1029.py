# Generated by Django 3.1.2 on 2020-11-27 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='featured_video',
            field=models.TextField(blank=True, null=True),
        ),
    ]
