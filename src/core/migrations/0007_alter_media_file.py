# Generated by Django 3.2.13 on 2023-06-21 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_daterelevanceindex_rank'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='file',
            field=models.CharField(max_length=350),
        ),
    ]