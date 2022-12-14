# Generated by Django 3.2.13 on 2022-07-12 13:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShowroomObjectHistory',
            fields=[
                ('showroom_id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('object_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.showroomobject')),
            ],
        ),
    ]
