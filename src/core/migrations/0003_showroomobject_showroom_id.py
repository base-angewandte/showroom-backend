# Generated by Django 3.2.13 on 2022-07-14 08:27

from django.db import migrations, models

from general.utils import slugify


def generate_showroom_ids(apps, schema_editor):
    # noinspection PyPep8Naming
    ShowroomObject = apps.get_model('core', 'ShowroomObject')
    for obj in ShowroomObject.objects.all():
        if obj.type in ['per', 'ins', 'dep']:
            obj.showroom_id = f'{slugify(obj.title)}-{obj.id}'
        else:
            obj.showroom_id = obj.id
        obj.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_showroomobjecthistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='showroomobject',
            name='showroom_id',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.RunPython(code=generate_showroom_ids, reverse_code=noop),
        migrations.AlterField(
            model_name='showroomobject',
            name='showroom_id',
            field=models.CharField(default='', max_length=255, unique=True),
        )
    ]
