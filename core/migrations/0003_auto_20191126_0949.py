# Generated by Django 2.2.6 on 2019-11-26 09:49

import core.models.shared
from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_userprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileField',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('key', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=512)),
                ('category', models.CharField(blank=True, max_length=512, null=True)),
                ('field_type', models.CharField(choices=[('select_field', 'SelectField'), ('date_field', 'DateField'), ('html_field', 'HTMLField'), ('multi_select_field', 'MultiSelectField'), ('text_field', 'TextField')], default='text_field', max_length=24)),
                ('field_options', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=512), blank=True, default=list, size=None)),
                ('is_editable_by_user', models.BooleanField(default=True)),
                ('is_filter', models.BooleanField(default=False)),
            ],
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='_profile', to='user.User'),
        ),
        migrations.CreateModel(
            name='UserProfileField',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('value', models.CharField(max_length=4096)),
                ('read_access', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), blank=True, default=core.models.shared.read_access_default, size=None)),
                ('write_access', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), blank=True, default=core.models.shared.write_access_default, size=None)),
                ('profile_field', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.ProfileField')),
                ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.UserProfile')),
            ],
        ),
    ]
