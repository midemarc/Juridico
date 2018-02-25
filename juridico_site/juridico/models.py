from django.db import models

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
            ("d", "date")
        ),
        max_length=1
    )
    methode = models.CharField(max_length=32, default="")

class Variable(models.Model):
    vid = models.AutoField(primary_key=True)
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

class Reponse(models.Model):
    repid = models.AutoField(primary_key=True)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    client = models.ForeignKey("Client", on_delete=models.CASCADE)
    requete = models.ForeignKey("Requete", on_delete=models.CASCADE)
    reponse = models.CharField(max_length=1024)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modif = models.DateTimeField(auto_now=True)

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
    rrid = models.IntegerField(default=-1)
    poid = models.FloatField(default=0.)
