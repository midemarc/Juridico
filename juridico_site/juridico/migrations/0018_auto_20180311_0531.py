# Generated by Django 2.0.2 on 2018-03-11 05:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('juridico', '0017_remove_organisation_site_web'),
    ]

    operations = [
        migrations.CreateModel(
            name='Educaloi',
            fields=[
                ('resid', models.AutoField(primary_key=True, serialize=False, unique=True)),
                ('description', models.TextField(blank=True)),
                ('commentaires', models.TextField(blank=True)),
                ('nom', models.CharField(blank=True, max_length=256)),
                ('url', models.CharField(max_length=1024)),
                ('artid', models.IntegerField(unique=True)),
                ('categorie_educaloi', models.CharField(max_length=256)),
                ('tags', models.ManyToManyField(blank=True, to='juridico.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EducaloiCategsPonderees',
            fields=[
                ('ecpid', models.AutoField(primary_key=True, serialize=False)),
                ('rang', models.IntegerField()),
                ('distance', models.FloatField()),
                ('article', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='juridico.Educaloi')),
                ('categorie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='juridico.Categorie')),
            ],
        ),
        migrations.AddField(
            model_name='client',
            name='types_de_droit',
            field=models.ManyToManyField(blank=True, help_text="Les types de droit qui caractérisent l'expérience juridique de la personne", to='juridico.Categorie'),
        ),
    ]
