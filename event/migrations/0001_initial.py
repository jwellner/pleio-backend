# Generated by Django 2.2.6 on 2019-10-21 20:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('file', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('entity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.Entity')),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField()),
                ('rich_description', models.TextField(blank=True, null=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('featured_video', models.CharField(blank=True, max_length=256, null=True)),
                ('featured_position_y', models.IntegerField(default=0)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('location', models.CharField(default='', max_length=256)),
                ('external_link', models.CharField(default='', max_length=256)),
                ('max_attendees', models.PositiveIntegerField(blank=True, null=True)),
                ('rsvp', models.BooleanField(default=False)),
                ('attend_event_without_account', models.BooleanField(default=False)),
                ('featured_image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='file.FileFolder')),
            ],
            options={
                'ordering': ['-created_at'],
            },
            bases=('core.entity', models.Model),
        ),
        migrations.CreateModel(
            name='EventAttendeeRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('email', models.CharField(max_length=256)),
                ('code', models.CharField(max_length=36)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='event.Event')),
            ],
        ),
        migrations.CreateModel(
            name='EventAttendee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('accept', 'Accept'), ('maybe', 'Maybe'), ('reject', 'Reject')], max_length=16)),
                ('name', models.CharField(blank=True, max_length=256, null=True)),
                ('email', models.CharField(blank=True, max_length=256, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendees', to='event.Event')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
