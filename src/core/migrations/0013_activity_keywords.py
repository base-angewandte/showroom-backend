# Generated by Django 2.2.16 on 2021-07-22 04:45

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20210715_2126'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='keywords',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]