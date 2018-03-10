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
    type_de_tag = models.ForeignKey("TagType", blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.type_de_tag ==None:
            return "(%d) %s" % (self.tid,self.nom)
        else:
            return "(%d) %s → %s" % (self.tid,self.type_de_tag.nom, self.nom)


class TagType(models.Model):
    ttid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=256)
    def __str__(self):
        return "(%d) %s" % (self.ttid,self.nom)

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

class Categorie(models.Model):
    catid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=1024)
    parent = models.ManyToManyField("Categorie")

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
    resid = models.AutoField(primary_key=True, unique=True)
    description = models.TextField(blank=True)
    tags = models.ManyToManyField("Tag", blank=True)
    commentaires = models.TextField(blank=True)

    class Meta:
        abstract = True

class Organisation(Ressource):
    nom = models.CharField(max_length=256)
    url = models.CharField(max_length=1024, blank=True)
    code_postal = models.CharField(
        max_length=6,
        blank=True,
        help_text = "Sert à géolocaliser"
    )
    adresse = models.CharField(max_length=1024, blank=True)
    courriel = models.CharField(max_length=1024, blank=True)
    appartenance = models.CharField(
        max_length=1024,
        blank=True,
        help_text = "Par exemple, pour un·e avocat·e ou notaire, son cabinet."
    )
    telephone = models.CharField(max_length=64, blank=True)
    telecopieur = models.CharField(max_length=64, blank=True)
    heures_ouverture = models.TextField(blank=True)

    def __str__(self):
        return f"({self.resid}) {self.nom}"

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
    code_postal = models.CharField(max_length=6, blank=True)

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
    poid = models.FloatField(default=0.)

    def get_ressource(self):
        return Ressource.objects.get(resid=self.resid)
