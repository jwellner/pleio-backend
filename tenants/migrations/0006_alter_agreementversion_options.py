# Generated by Django 3.2.15 on 2022-10-06 09:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0005_agreement_agreementaccept_agreementversion'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='agreementversion',
            options={'ordering': ['-created_at']},
        ),
    ]
