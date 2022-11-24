# Generated by Django 3.2.16 on 2022-11-19 14:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0079_videocall_videocallguest'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileSet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.profilefield')),
                ('users', models.ManyToManyField(related_name='profile_sets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
