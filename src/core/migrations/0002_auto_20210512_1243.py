# Generated by Django 2.2.16 on 2021-05-12 10:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='activity',
            old_name='type',
            new_name='source_repo_data',
        ),
    ]