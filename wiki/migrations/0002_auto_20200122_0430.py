# Generated by Django 2.2.6 on 2020-01-22 04:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wiki',
            options={'ordering': ['position', '-created_at']},
        ),
        migrations.AddField(
            model_name='wiki',
            name='position',
            field=models.IntegerField(default=0),
        ),
    ]
