# Generated by Django 3.1.7 on 2021-03-24 09:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0001_initial'),
        ('core', '0020_userprofile_picture_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='picture_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='picture_file', to='file.filefolder'),
        ),
    ]
