# Generated by Django 3.2.6 on 2022-02-02 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_alter_userprofilefield_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='resizedimage',
            name='message',
            field=models.TextField(default=''),
        ),
    ]
