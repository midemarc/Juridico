# Generated by Django 2.0.2 on 2018-03-11 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('juridico', '0018_auto_20180311_0531'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='code_postal',
            field=models.CharField(blank=True, max_length=6),
        ),
        migrations.AddField(
            model_name='client',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='organisation',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='organisation',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
