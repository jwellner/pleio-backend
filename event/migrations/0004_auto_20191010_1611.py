# Generated by Django 2.2.6 on 2019-10-10 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0003_auto_20191002_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventattendee',
            name='state',
            field=models.CharField(choices=[('accept', 'Accept'), ('maybe', 'Maybe'), ('reject', 'Reject')], max_length=16),
        ),
    ]