# Generated by Django 2.2.27 on 2022-03-24 14:25

import core.models
import core.validators
import django.contrib.postgres.fields.jsonb
import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models
import django.db.models.deletion
import general.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ShowroomObject',
            fields=[
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_changed', models.DateTimeField(auto_now=True)),
                ('id', general.models.ShortUUIDField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('subtext', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('type', models.CharField(choices=[('act', 'activity'), ('alb', 'album'), ('per', 'person'), ('ins', 'institution'), ('dep', 'department')], max_length=3)),
                ('list', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('primary_details', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('secondary_details', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('locations', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('source_repo_object_id', models.CharField(max_length=255)),
                ('source_repo_owner_id', models.CharField(blank=True, max_length=255, null=True)),
                ('source_repo_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('date_synced', models.DateTimeField(editable=False, null=True)),
                ('belongs_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.ShowroomObject')),
                ('relations_to', models.ManyToManyField(blank=True, related_name='relations_from', to='core.ShowroomObject')),
            ],
            options={
                'ordering': ('-date_created',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SourceRepository',
            fields=[
                ('id', models.PositiveSmallIntegerField(primary_key=True, serialize=False)),
                ('label_institution', models.CharField(max_length=255)),
                ('label_repository', models.CharField(max_length=255)),
                ('url_institution', models.CharField(max_length=255)),
                ('url_repository', models.CharField(max_length=255)),
                ('icon', models.CharField(blank=True, max_length=255)),
                ('api_key', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='ActivityDetail',
            fields=[
                ('showroom_object', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.ShowroomObject')),
                ('activity_type', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('keywords', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EntityDetail',
            fields=[
                ('showroom_object', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.ShowroomObject')),
                ('expertise', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('showcase', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, validators=[core.validators.validate_showcase])),
                ('photo', models.CharField(blank=True, max_length=255)),
                ('list', django.contrib.postgres.fields.jsonb.JSONField(default=dict, validators=[core.validators.validate_entity_list])),
                ('list_ordering', django.contrib.postgres.fields.jsonb.JSONField(default=core.models.get_default_list_ordering, validators=[core.validators.validate_list_ordering])),
            ],
        ),
        migrations.CreateModel(
            name='TextSearchIndex',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('language', models.CharField(max_length=255)),
                ('text', models.TextField(default='')),
                ('text_vector', django.contrib.postgres.search.SearchVectorField(null=True)),
                ('showroom_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ShowroomObject')),
            ],
        ),
        migrations.AddField(
            model_name='showroomobject',
            name='source_repo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.SourceRepository'),
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', general.models.ShortUUIDField(primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('i', 'Image'), ('a', 'Audio'), ('v', 'Video'), ('d', 'Document'), ('x', 'Undefined')], max_length=1)),
                ('file', models.CharField(max_length=255)),
                ('mime_type', models.CharField(max_length=255)),
                ('exif', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('license', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('specifics', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('source_repo_media_id', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('showroom_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ShowroomObject')),
            ],
        ),
        migrations.CreateModel(
            name='DateSearchIndex',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('showroom_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ShowroomObject')),
            ],
        ),
        migrations.CreateModel(
            name='DateRangeSearchIndex',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date_from', models.DateField()),
                ('date_to', models.DateField()),
                ('showroom_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ShowroomObject')),
            ],
        ),
        migrations.AddIndex(
            model_name='textsearchindex',
            index=django.contrib.postgres.indexes.GinIndex(fields=['text_vector'], name='core_textse_text_ve_25c111_gin'),
        ),
        migrations.AddField(
            model_name='activitydetail',
            name='featured_medium',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='featured_by', to='core.Media'),
        ),
    ]
