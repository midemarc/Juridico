# Generated by Django 2.0.2 on 2018-02-25 16:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('juridico', '0003_auto_20180225_1553'),
    ]

    operations = [
        migrations.CreateModel(
            name='RessourceDeRequete',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rrid', models.IntegerField(default=-1)),
                ('poid', models.FloatField(default=0.0)),
                ('requete', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='juridico.Requete')),
            ],
        ),
    ]
