# Generated by Django 2.2.2 on 2019-09-19 15:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20190919_1508'),
        ('question', '0002_auto_20190919_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='best_answer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Comment'),
        ),
    ]
