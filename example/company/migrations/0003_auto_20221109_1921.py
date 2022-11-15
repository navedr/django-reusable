# Generated by Django 2.0.5 on 2022-11-09 19:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0002_person_position'),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Concert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='MusicianConcert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.City')),
                ('concert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.Concert')),
                ('musician', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.Musician')),
            ],
        ),
        migrations.AddField(
            model_name='musician',
            name='concerts',
            field=models.ManyToManyField(through='company.MusicianConcert', to='company.Concert'),
        ),
    ]
