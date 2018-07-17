# Generated by Django 2.0 on 2018-05-13 19:54

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('read_access', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32), blank=True, default=[], size=None)),
                ('write_access', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32), blank=True, default=[], size=None)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256), blank=True, default=[], size=None)),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField()),
            ],
            options={
                'ordering': ['created_at'],
                'abstract': False,
            },
        ),
    ]