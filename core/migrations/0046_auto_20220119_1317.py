# Generated by Django 3.2.6 on 2022-01-19 12:17

from django.db import migrations, models

def set_initial_status(apps, schema_editor):
    ResizedImage = apps.get_model('core', 'ResizedImage')
    ResizedImage.objects.all().update(status='OK')

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0045_resizedimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='resizedimage',
            name='status',
            field=models.CharField(default='PENDING', max_length=255),
        ),
        migrations.AddField(
            model_name='resizedimage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RunPython(set_initial_status, migrations.RunPython.noop),
    ]
