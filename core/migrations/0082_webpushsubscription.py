# Generated by Django 3.2.16 on 2022-12-19 12:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0081_group_content_presets'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebPushSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('browser', models.CharField(max_length=100)),
                ('endpoint', models.URLField(max_length=800)),
                ('auth', models.CharField(max_length=100)),
                ('p256dh', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='web_push_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
