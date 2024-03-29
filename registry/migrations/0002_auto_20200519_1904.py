# Generated by Django 3.0.5 on 2020-05-19 19:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assay',
            name='url',
        ),
        migrations.RemoveField(
            model_name='media',
            name='url',
        ),
        migrations.RemoveField(
            model_name='strain',
            name='url',
        ),
        migrations.AlterField(
            model_name='sample',
            name='inducer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='registry.Inducer'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='row',
            field=models.IntegerField(),
        ),
    ]
