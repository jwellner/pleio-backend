# Generated by Django 3.2.16 on 2022-12-14 16:58

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0080_profileset'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalContentSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('plural_name', models.CharField(max_length=256)),
                ('handler_id', models.CharField(max_length=128)),
                ('settings', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ('handler_id', 'name'),
            },
        ),
        migrations.CreateModel(
            name='ExternalContentFetchLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('success', models.BooleanField()),
                ('message', models.TextField()),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='external_content.externalcontentsource')),
            ],
        ),
        migrations.CreateModel(
            name='ExternalContent',
            fields=[
                ('entity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.entity')),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField()),
                ('remote_id', models.CharField(max_length=256)),
                ('canonical_url', models.URLField()),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='external_content.externalcontentsource')),
            ],
            options={
                'abstract': False,
            },
            bases=('core.entity',),
        ),
    ]
