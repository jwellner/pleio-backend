# Generated by Django 3.0.7 on 2020-07-14 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wiki',
            fields=[
                ('entity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.Entity')),
                ('position', models.IntegerField(default=0)),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField()),
                ('rich_description', models.TextField(blank=True, null=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='wiki.Wiki')),
            ],
            options={
                'ordering': ['position', '-created_at'],
            },
            bases=('core.entity', models.Model),
        ),
    ]
