# Generated by Django 3.1.2 on 2020-10-21 12:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_auto_20201013_1451'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='login_count',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
    ]
