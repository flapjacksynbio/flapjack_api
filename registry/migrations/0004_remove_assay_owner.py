# Generated by Django 3.0.5 on 2020-07-18 07:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0003_auto_20200706_0940'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assay',
            name='owner',
        ),
    ]
