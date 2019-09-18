# Generated by Django 2.2.2 on 2019-09-11 07:32

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0002_vote'),
    ]

    operations = [
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('object_id', models.UUIDField(default=uuid.uuid4)),
                ('key', models.CharField(choices=[('bookmarked', 'Bookmarked'), ('voted', 'Voted')], default='bookmarked', max_length=16)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('content_type', 'object_id', 'user')},
            },
        ),
        migrations.DeleteModel(
            name='Vote',
        ),
    ]