# Generated by Django 2.0.2 on 2018-03-11 10:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('juridico', '0020_ressourcederequete_distance'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategDocumentation',
            fields=[
                ('ecpid', models.AutoField(primary_key=True, serialize=False)),
                ('rang', models.IntegerField()),
                ('distance', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='DocuSource',
            fields=[
                ('dcid', models.AutoField(primary_key=True, serialize=False)),
                ('nom', models.CharField(max_length=256)),
                ('url', models.CharField(blank=True, max_length=1024, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='educaloi',
            name='tags',
        ),
        migrations.RemoveField(
            model_name='educaloicategsponderees',
            name='article',
        ),
        migrations.RemoveField(
            model_name='educaloicategsponderees',
            name='categorie',
        ),
        migrations.AddField(
            model_name='documentation',
            name='artid_educaloi',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='documentation',
            name='categorie_educaloi',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.DeleteModel(
            name='Educaloi',
        ),
        migrations.DeleteModel(
            name='EducaloiCategsPonderees',
        ),
        migrations.AddField(
            model_name='categdocumentation',
            name='article',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='juridico.Documentation'),
        ),
        migrations.AddField(
            model_name='categdocumentation',
            name='categorie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='juridico.Categorie'),
        ),
        migrations.AddField(
            model_name='documentation',
            name='nom_source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='juridico.DocuSource'),
        ),
    ]
