from django.db import models
from datetime import datetime, timedelta, date
import re

# Create your models here.

item_html = """<div class="item{extra_class}">
<h4><a href="{url}">{titre}</a></h4>
<div class="description"></div>
</div>"""


class Tag(models.Model):
    tid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=256)

class Client(models.Model):
    pseudo = models.CharField(max_length=128, unique=True)
    cid = models.AutoField(primary_key=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modif = models.DateTimeField(auto_now=True)
    courriel = models.EmailField()
    tags = models.ManyToManyField("Tag", blank=True)

class Question(models.Model):
    qid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=128, unique=True)
    question = models.TextField()
    reponse_type = models.CharField(
        choices = (
            ("t", "textuel"),
            ("e", "entier numérique"),
            ("f", "numérique à décimales"),
            ("b", "booléen"),
            ("d", "date"),
            ("l", "liste")
        ),
        max_length=1
    )
    contenu_liste = models.TextField(blank=True, default="")

    def options(self) -> list:
        if '\r\n' in self.contenu_liste:
            return self.contenu_liste.split('\r\n')
        return []


class Variable(models.Model):
    vid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=32, unique=True)
    valeur = models.CharField(max_length=1024)
    requete = models.ForeignKey("Requete", on_delete=models.CASCADE)

class Reponse(models.Model):
    repid = models.AutoField(primary_key=True)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    requete = models.ForeignKey("Requete", on_delete=models.CASCADE)
    reponse = models.CharField(max_length=1024)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modif = models.DateTimeField(auto_now=True)

    def get_value(self):
        rtype = self.question.reponse_type
        if r == "t" or r == "l": return self.reponse
        elif r=="e": return int(self.reponse)
        elif r=="f": return float(self.reponse)
        elif r=="b":
            r = self.reponse.strip().lower()
            if r in ("y", "o", "yes", "oui", "true", "vrai", "1"):
                return True
            elif r in ("n", "non", "no", "false", "0"):
                return False
        elif r=="d":
            # On assume l'ordre français pour les dates:
            d,m,y = tuple(int(i) for i in re.split("[/-. ]+", self.reponse.strip()))
            return date(y,m,d)

class Requete(models.Model):
    reqid = models.AutoField(primary_key=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modif = models.DateTimeField(auto_now=True)

    description_cas = models.TextField()
    client = models.ForeignKey("Client", on_delete=models.CASCADE)

# Types de ressources

class Ressource(models.Model):
    resid = models.AutoField(primary_key=True, default=0, unique=True)
    description = models.TextField(default="")
    tags = models.ManyToManyField("Tag", blank=True)

    class Meta:
        abstract = True

class Organisation(Ressource):
    nom = models.CharField(max_length=256)
    url = models.CharField(max_length=1024)

    def to_resultats(self):
        return item_html.format(
            url=self.url,
            titre=self.nom,
            description=self.description,
            extra_class=" organisation"
        )

class Documentation(Ressource):
    nom = models.CharField(max_length=256)
    url = models.CharField(max_length=1024)

    def to_resultats(self):
        return item_html.format(
            url=self.url,
            titre=self.nom,
            description=self.description,
            extra_class=" documentation"
        )

class Camarade(Ressource):
    client = models.ForeignKey("Client", on_delete=models.CASCADE)

    def to_resultats(self):
        return item_html.format(
            url="",
            titre=self.nom,
            description=self.description,
            extra_class=" camarade"
        )

class Direction(Ressource):
    quand = models.CharField(max_length=256)

    def to_resultats(self):
        return """<tr>
        <td>{quand}</td>
        <td>{description}</td>
        </tr>""".format(description=self.description, quand=self.quand)


class RessourceDeRequete(models.Model):
    rrid = models.AutoField(primary_key=True)
    requete = models.ForeignKey("Requete", on_delete=models.CASCADE)
    resid = models.IntegerField(default=-1)
    poids = models.FloatField(default=0.)

    def get_ressource(self):
        return Ressource.objects.get(resid=self.resid)
