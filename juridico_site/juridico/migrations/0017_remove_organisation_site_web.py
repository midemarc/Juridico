# Generated by Django 2.0.2 on 2018-03-10 07:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('juridico', '0016_auto_20180310_0536'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organisation',
            name='site_web',
        ),
    ]
