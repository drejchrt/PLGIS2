# Generated by Django 3.2.5 on 2022-01-03 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plgis', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='circuit',
            name='substation_end',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='circuit',
            name='substation_start',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
