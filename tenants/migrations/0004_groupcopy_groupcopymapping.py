# Generated by Django 3.2.6 on 2022-04-19 15:46

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_client_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupCopy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_tenant', models.CharField(max_length=200)),
                ('target_tenant', models.CharField(max_length=200)),
                ('action_user_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('source_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('target_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('task_id', models.CharField(max_length=200, null=True)),
                ('task_state', models.CharField(choices=[('PENDING', 'PENDING'), ('STARTED', 'STARTED'), ('RETRY', 'RETRY'), ('FAILURE', 'FAILURE'), ('SUCCESS', 'SUCCESS')], default='PENDING', max_length=16)),
                ('task_response', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GroupCopyMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity_type', models.CharField(max_length=200)),
                ('source_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('target_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('copy', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mapping', to='tenants.groupcopy')),
            ],
        ),
    ]
