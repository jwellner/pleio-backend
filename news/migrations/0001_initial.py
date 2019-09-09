# Generated by Django 2.2.2 on 2019-09-09 08:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('entity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.Entity')),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField()),
                ('is_featured', models.BooleanField(default=False)),
                ('featured_video', models.CharField(blank=True, max_length=256, null=True)),
                ('featured_position_y', models.IntegerField(default=0)),
                ('featured_image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.FileFolder')),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=('core.entity',),
        ),
    ]
