# Generated by Django 3.2.6 on 2021-08-23 15:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0003_auto_20210810_1405'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scanincident',
            name='file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scan_incidents', to='file.filefolder'),
        ),
    ]
