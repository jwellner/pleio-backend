# Generated by Django 3.2.16 on 2022-12-22 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('external_content', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalcontent',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
