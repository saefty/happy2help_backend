# Generated by Django 2.1.2 on 2018-11-21 13:17

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Event', '0004_auto_20181116_1743'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='end',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='event',
            name='start',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now),
        ),
    ]
