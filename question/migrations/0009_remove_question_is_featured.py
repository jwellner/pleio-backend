# Generated by Django 3.2.6 on 2022-02-03 14:53

from django.db import migrations

def forward_update_entity(apps, schema_editor):
    pass

def reverse_update_entity(apps, schema_editor):
    Question = apps.get_model('question', 'Question')
    Question.objects.filter(tmp_is_featured=True).update(is_featured=True)

class Migration(migrations.Migration):

    dependencies = [
        ('question', '0008_rename_is_featured_question_old_is_featured'),
    ]

    run_before = [
        ('core', '0051_auto_20220203_1553'),
    ]

    operations = [
        migrations.RunPython(forward_update_entity, reverse_update_entity),
        migrations.RemoveField(
            model_name='question',
            name='is_featured',
        ),
    ]