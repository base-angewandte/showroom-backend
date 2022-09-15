from django.db import migrations, models

from general.utils import slugify

from core.models import ShowroomObject, ShowroomObjectHistory


def shorten_ids(apps, schema_editor):
    for obj in ShowroomObject.objects.all():
        if obj.type in ['per', 'ins', 'dep']:
            old_id = obj.showroom_id
            obj.generate_showroom_id()
            if obj.showroom_id != old_id:
                obj.save()
                ShowroomObjectHistory.objects.create(
                    showroom_id=old_id,
                    object=obj,
                )


def reverse_shorten_ids(apps, schema_editor):
    for obj in ShowroomObject.objects.all():
        if obj.type in ['per', 'ins', 'dep']:
            old_id = obj.showroom_id
            obj.showroom_id = f'{slugify(obj.title)}-{obj.id}'
            if obj.showroom_id != old_id:
                obj.save()
                try:
                    hist = ShowroomObjectHistory.objects.get(
                        showroom_id=obj.showroom_id,
                        object=obj,
                    )
                    hist.delete()
                except:
                    pass



class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_rename_object_id_showroomobjecthistory_object')
    ]

    operations = [
        migrations.RunPython(code=shorten_ids, reverse_code=reverse_shorten_ids),
    ]
