# Generated by Django 3.2.16 on 2023-01-12 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0025_attendee_welcome_message'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventattendee',
            options={'ordering': ('updated_at',)},
        ),
        migrations.AlterField(
            model_name='event',
            name='attendee_welcome_mail_content',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='attendee_welcome_mail_subject',
            field=models.CharField(blank=True, default='', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='eventattendee',
            name='state',
            field=models.CharField(blank=True, choices=[('accept', 'Accepted'), ('maybe', 'Maybe'), ('reject', 'Rejected'), ('waitinglist', 'At waitinglist')], max_length=16, null=True),
        ),
    ]
