# Generated by Django 3.1.8 on 2021-06-01 12:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0003_auto_20200806_1637'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={'ordering': ['position', 'published']},
        ),
    ]
