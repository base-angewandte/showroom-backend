# Generated by Django 3.2.13 on 2022-07-14 13:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_showroomobject_showroom_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='showroomobjecthistory',
            old_name='object_id',
            new_name='object',
        ),
    ]
