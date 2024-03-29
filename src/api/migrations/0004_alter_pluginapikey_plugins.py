# Generated by Django 3.2.13 on 2023-07-18 15:06

import api.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20220712_1559'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pluginapikey',
            name='plugins',
            field=models.JSONField(blank=True, default=list, help_text='JSON list of plugins that can be used with this key. See API plugins section in the docs for available plugins.', validators=[api.models.validate_plugins]),
        ),
    ]
