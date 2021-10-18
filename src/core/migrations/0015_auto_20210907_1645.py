# Generated by Django 2.2.16 on 2021-09-07 14:45

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_activity_source_repo_data_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivitySearch',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('language', models.CharField(max_length=255)),
                ('text', models.TextField(default='')),
                ('text_vector', django.contrib.postgres.search.SearchVectorField(null=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Activity')),
            ],
        ),
        migrations.AddIndex(
            model_name='activitysearch',
            index=django.contrib.postgres.indexes.GinIndex(fields=['text_vector'], name='core_activi_text_ve_024163_gin'),
        ),
    ]
