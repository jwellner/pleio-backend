# Generated by Django 3.2.6 on 2021-11-30 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_alter_blog_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='abstract',
            field=models.TextField(blank=True, null=True),
        ),
    ]