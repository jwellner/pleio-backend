# Generated by Django 2.2.11 on 2020-03-09 14:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0004_auto_20200115_0959'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='column',
            name='parent_id',
        ),
        migrations.RemoveField(
            model_name='row',
            name='parent_id',
        ),
        migrations.AddField(
            model_name='column',
            name='row',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='columns', to='cms.Row'),
        ),
    ]