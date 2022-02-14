# Generated by Django 3.2.6 on 2022-02-03 14:03

from django.db import migrations


def forward_update_entity(apps, schema_editor):
    Blog = apps.get_model('blog', 'Blog')
    Blog.objects.filter(is_featured=True).update(tmp_is_featured=True)
    Blog.objects.filter(is_recommended=True).update(tmp_is_recommended=True)

def reverse_update_entity(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_blog_abstract'),
        ('core', '0050_auto_20220203_1503')
    ]

    operations = [
        migrations.RunPython(forward_update_entity, reverse_update_entity),
    ]
