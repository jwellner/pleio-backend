# Generated by Django 3.2.14 on 2022-08-25 12:41

from django.db import migrations

def undo_is_folder(apps, schema_editor):
    # pylint: disable=unused-argument
    FileFolder = apps.get_model('file', 'FileFolder')
    FileFolder.objects.filter(type="Folder").update(is_folder=True)

class Migration(migrations.Migration):

    dependencies = [
        ('file', '0009_filefolder_type'),
    ]

    operations = [
        migrations.RunPython(
            migrations.RunPython.noop,
            undo_is_folder
        ),
        migrations.RemoveField(
            model_name='filefolder',
            name='is_folder',
        ),
    ]