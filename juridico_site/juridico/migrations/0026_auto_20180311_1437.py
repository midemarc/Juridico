# Generated by Django 2.0.2 on 2018-03-11 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('juridico', '0025_merge_20180311_1436'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ressourcederequete',
            old_name='poids',
            new_name='poid',
        ),
        migrations.AlterField(
            model_name='direction',
            name='variables',
            field=models.TextField(blank=True, default='', help_text='Les variables sont séparées par des espaces'),
        ),
    ]
