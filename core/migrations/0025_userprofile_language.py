# Generated by Django 3.1.8 on 2021-06-01 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_entity_is_pinned'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='language',
            field=models.CharField(blank=True, default=None, max_length=10, null=True),
        ),
    ]