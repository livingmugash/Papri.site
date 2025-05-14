# api/migrations/0002_add_fulltext_search.py
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'), # Assuming this is your first migration
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE FULLTEXT INDEX idx_api_yourmodel_yourfield ON api_yourmodel(yourfield);",
            # Replace api_yourmodel with your actual table name (appname_modelname)
            # and yourfield with the field you want to index.
            reverse_sql="ALTER TABLE api_yourmodel DROP INDEX idx_api_yourmodel_yourfield;"
        )
    ]
