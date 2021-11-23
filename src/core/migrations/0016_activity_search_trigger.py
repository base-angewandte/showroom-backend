# Generated by Django 2.2.16 on 2021-09-07 13:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20210907_1645'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
              CREATE TRIGGER text_column_trigger
              BEFORE INSERT OR UPDATE OF text
              ON core_activitysearch
              FOR EACH ROW EXECUTE PROCEDURE
              tsvector_update_trigger(
                text_vector, 'pg_catalog.simple', text
              );
    
              UPDATE core_activitysearch SET text_vector = NULL;
            ''',

            reverse_sql='''
              DROP TRIGGER IF EXISTS text_column_trigger
              ON core_activitysearch;
            '''
        ),
    ]