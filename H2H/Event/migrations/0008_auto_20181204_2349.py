# Generated by Django 2.1.2 on 2018-12-04 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Event', '0007_auto_20181122_1719'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='job',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='job',
            name='canceled',
        ),
    ]
