# Generated by Django 2.2.2 on 2019-09-23 12:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('question', '0003_question_best_answer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='best_answer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Comment'),
        ),
    ]