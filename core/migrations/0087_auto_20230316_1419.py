# Generated by Django 3.2.18 on 2023-03-16 13:19

from django.db import migrations, models

def set_notifications_enabled(apps, schema_editor):
    GroupMembership = apps.get_model('core', 'GroupMembership')
    GroupMembership.objects.filter(notification_mode="disable").update(is_notifications_enabled=False)

def reverse_notifications_enabled(apps, schema_editor):
    GroupMembership = apps.get_model('core', 'GroupMembership')
    GroupMembership.objects.filter(is_notifications_enabled=False).update(notification_mode="disable")

def set_notification_direct_mail(apps, schema_editor):
    GroupMembership = apps.get_model('core', 'GroupMembership')
    GroupMembership.objects.filter(notification_mode="direct").update(is_notification_direct_mail_enabled=True)

def reverse_notification_direct_mail(apps, schema_editor):
    GroupMembership = apps.get_model('core', 'GroupMembership')
    GroupMembership.objects.filter(is_notification_direct_mail_enabled=True).update(notification_mode="direct")

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0086_file_scan_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmembership',
            name='is_notification_direct_mail_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='groupmembership',
            name='is_notification_push_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='groupmembership',
            name='is_notifications_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(set_notifications_enabled, reverse_notifications_enabled),
        migrations.RunPython(set_notification_direct_mail, reverse_notification_direct_mail),
    ]
