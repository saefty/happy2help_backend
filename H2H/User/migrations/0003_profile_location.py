# Generated by Django 2.1.2 on 2018-11-21 11:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Location', '0001_initial'),
        ('User', '0002_auto_20181116_1743'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='location',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='Location.Location'),
        ),
    ]