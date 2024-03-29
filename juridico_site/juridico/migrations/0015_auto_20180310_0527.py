# Generated by Django 2.0.2 on 2018-03-10 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('juridico', '0014_auto_20180310_0518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='camarade',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='camarade',
            name='resid',
            field=models.AutoField(primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='direction',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='direction',
            name='resid',
            field=models.AutoField(primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='documentation',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='documentation',
            name='resid',
            field=models.AutoField(primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='resid',
            field=models.AutoField(primary_key=True, serialize=False, unique=True),
        ),
    ]
