# Generated by Django 3.2.16 on 2023-01-27 19:03

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0007_remove_client_elgg_database'),
        ('control', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ElasticsearchStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index_status', models.JSONField(null=True)),
                ('access_status', models.JSONField(null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('client', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='elasticsearch_status', to='tenants.client')),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
