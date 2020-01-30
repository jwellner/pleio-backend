# Generated by Django 2.2.6 on 2020-01-16 17:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_widget_page'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subgroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=512)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subgroups', to='core.Group')),
                ('members', models.ManyToManyField(related_name='subgroups', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]