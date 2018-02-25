from django.db import models

# Create your models here.

class Client(models.Model):
    pseudo = models.CharField(max_length=128, unique=True)
    cid = models.IntegerField(primary_key=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modif = models.DateTimeField(auto_now=True)
    courriel = models.EmailField()

class Question(models.Model):
    qid = models.IntegerField(primary_key=True)
    nom = models.CharField(max_length=128, unique=True)
    question = models.TextField()
    reponse_type = models.CharField(
        choices = (
            ("t", "textuel"),
            ("e", "entier numérique"),
            ("f", "numérique à décimales"),
            ("b", "booléen"),
            ("d", "date")
        ),
        max_length=1
    )
    methode = models.CharField(max_length=32, default="")

class Variable(models.Model):
    vid = models.IntegerField(primary_key=True)
    nom = models.CharField(max_length=32)
    valeur = models.CharField(max_length=1024)
    requete = models.ForeignKey("Requete", on_delete=models.CASCADE)
    reponse_type = models.CharField(
        choices = (
            ("t", "textuel"),
            ("e", "entier numérique"),
            ("f", "numérique à décimales"),
            ("b", "booléen"),
            ("d", "date")
        ),
        max_length=1
    )

class Ressource(models.Model):
    resid = models.IntegerField(primary_key=True)
    requete = models.ForeignKey("Requete", on_delete=models.CASCADE)
    description = models.TextField()

class Organisation(Ressource):
    nom = models.CharField(max_length=256)
    url = models.CharField(max_length=1024)

class Documentation(Ressource):
    nom = models.CharField(max_length=256)
    url = models.CharField(max_length=1024)

class Camarade(Ressource):
    client = models.ForeignKey("Client", on_delete=models.CASCADE)

class Direction(models.Model):
    dirid = models.IntegerField(primary_key=True)
    quand = models.CharField(max_length=256)
    contenu = models.TextField()


class Reponse(models.Model):
    repid = models.IntegerField(primary_key=True)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    client = models.ForeignKey("Client", on_delete=models.CASCADE)
    requete = models.ForeignKey("Requete", on_delete=models.CASCADE)
    reponse = models.CharField(max_length=1024)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modif = models.DateTimeField(auto_now=True)

class Requete(models.Model):
    reqid = models.IntegerField(primary_key=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modif = models.DateTimeField(auto_now=True)
    description_cas = models.TextField()
    client = models.ForeignKey("Client", on_delete=models.CASCADE)
