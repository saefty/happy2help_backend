# Generated by Django 2.1.2 on 2018-11-21 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Event', '0005_auto_20181121_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='end',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='event',
            name='start',
            field=models.DateTimeField(),
        ),
    ]
