# Generated by Django 2.0.5 on 2022-06-29 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Error',
            fields=[
                ('hash', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('host', models.CharField(max_length=1024)),
                ('path', models.CharField(max_length=4096)),
                ('method', models.CharField(max_length=64)),
                ('request_data', models.TextField()),
                ('exception_name', models.CharField(max_length=256)),
                ('traceback', models.TextField()),
                ('count', models.IntegerField(default=0)),
                ('created_on', models.DateTimeField(auto_now=True)),
                ('last_seen', models.DateTimeField(auto_now=True, db_index=True)),
            ],
        ),
    ]