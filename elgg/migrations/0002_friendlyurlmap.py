# Generated by Django 3.1.7 on 2021-03-25 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elgg', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FriendlyUrlMap',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('object_id', models.UUIDField()),
                ('url', models.URLField(max_length=1024, unique=True)),
            ],
        ),
    ]
