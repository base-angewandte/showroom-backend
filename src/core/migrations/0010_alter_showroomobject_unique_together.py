# Generated by Django 3.2.13 on 2022-04-24 11:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20220424_1210'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='showroomobject',
            unique_together={('source_repo', 'source_repo_object_id')},
        ),
    ]