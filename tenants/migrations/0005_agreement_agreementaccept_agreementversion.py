# Generated by Django 3.2.14 on 2022-07-23 12:21

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_groupcopy_groupcopymapping'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agreement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='AgreementVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('document', models.FileField(upload_to='agreements')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('agreement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='tenants.agreement')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='AgreementAccept',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accept_name', models.CharField(max_length=100)),
                ('accept_user_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('agreement_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accepted', to='tenants.agreementversion')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tenants.client')),
            ],
        ),
    ]
