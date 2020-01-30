# Generated by Django 2.2.6 on 2020-01-20 09:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_widget_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofilefield',
            name='profile_field',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profile_fields', to='core.ProfileField'),
        ),
        migrations.AlterField(
            model_name='userprofilefield',
            name='user_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_profile_fields', to='core.UserProfile'),
        ),
    ]