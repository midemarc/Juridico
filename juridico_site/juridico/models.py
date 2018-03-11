from django.db import models
from datetime import datetime, timedelta, date
import re
from geopy.distance import vincenty

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
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    code_postal = models.CharField(max_length=6, blank=True)
    types_de_droit = models.ManyToManyField(
        "Categorie",
        blank=True,
        help_text="Les types de droit qui caractérisent l'expérience juridique de la personne"
        )

    def entrer_geo_par_code_postal(self,code_postal):
        from juridico.methodes import cp2geo
        cp = re.sub("[^A-Z0-9]","",code_postal)
        g = cp2geo(cp)
        if g != None:
            self.latitude, self.longitude = g

    def plus_proche_organisations(self, topn=10):
        from juridico.methodes import plus_proche_org
        return plus_proche_org(self.latitude, self.longitude, topn=topn)

    def __str__(self):
        return "(%d) %s" % (self.cid, self.pseudo)

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

    def __str__(self):
        return "(%d) %s" % (self.qid, self.nom)

class Categorie(models.Model):
    # Les catégories concernent le contenu, là où les Tags concernent des
    # attributs divers (spécialité, langue, etc.) utiles pour l'usager·e
    catid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=1024)
    parent = models.ManyToManyField("Categorie")

    def __str__(self):
        return "(%d) %s" % (self.catid, self.nom)

class Variable(models.Model):
    vid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=32)
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
    ip = models.CharField(max_length=64, default="132.208.170.58")

    description_cas = models.TextField()
    description_vec = None
    client = models.ForeignKey("Client", on_delete=models.CASCADE)

    def get_desc_vector(self):
        from juridico.methodes import txt2text2vec
        if self.description_vec == None:
            self.description_vec = text2vec(self.description_cas)
        return self.description_vec

    def get_requete_educaloi(self, topn=10):
        return [i[1] for i in get_top_educaloi(self.get_desc_vector(), topn=topn)]


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
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
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

    def distance2pt(self, lat, long):
        "En km."
        if self.latitude == None or org.longitude == None:
            return None
        else:
            return vincenty((self.latitude,self.longitude),(lat,long)).km

class Documentation(Ressource):
    nom = models.CharField(max_length=256)
    url = models.CharField(max_length=1024)
    artid_educaloi = models.IntegerField(blank=True, null=True)
    categorie_educaloi = models.CharField(max_length=256, blank=True, null=True)
    nom_source = models.ForeignKey("DocuSource", blank=True, null=True, on_delete=models.SET_NULL)

    def to_resultats(self):
        return item_html.format(
            url=self.url,
            titre=self.nom,
            description=self.description,
            extra_class=" documentation"
        )

    def __str__(self):
        if self.nom_source != None:
            return "(%d) %s → %s" % (self.resid, self.nom_source.nom, self.nom)
        else:
            return "(%d) [source inconnue] → %s" % (self.resid, self.nom)

class CategDocumentation(models.Model):
    ecpid = models.AutoField(primary_key=True)
    rang = models.IntegerField()
    distance = models.FloatField()
    article = models.ForeignKey("Documentation", null=True, on_delete=models.CASCADE)
    categorie = models.ForeignKey("Categorie", on_delete=models.CASCADE)

class DocuSource(models.Model):
    dcid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=256)
    url = models.CharField(max_length=1024, blank=True, null=True)

    def __str__(self):
        return "(%d) %s" % (self.dcid, self.nom)

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

    def __str__(self):
        return "(%d) %s" % (self.resid, self.client.pseudo)

class Direction(Ressource):
    quand = models.CharField(max_length=256, blank=True, default="")
    identifiant = models.CharField(max_length=128, blank=True,null=True)
    variables = models.TextField(
        default="",
        help_text = "Les variables sont séparées par des espaces",
        blank=True
    )

    def get_description(self):
        "Donne la description formattée avec les variables pertinentes."
        if self.variables != "":
            from juridico.methodes import get_valeur
            vs = self.variables.split()
            d = dict(
                (v, get_valeur(self.requete, v)) for v in vs
            )
            desc = self.description.format(*d)
        else:
            desc=self.description
        return desc

    def to_resultats(self):
        "Pas trop sûr que c'est encore utile..."

        return """<tr>
        <td>{quand}</td>
        <td>{description}</td>
        </tr>""".format(description=desc, quand=self.quand)

    def __str__(self):
        if self.identifiant != None:
            return "(%d) %s" %(self.resid, self.identifiant)
        else:
            s = self.description[:64] +"…" if len(self.description)>64  else self.description
            return "(%d) %s" %(self.resid,s)

class RessourceDeRequete(models.Model):
    rrid = models.AutoField(primary_key=True)
    requete = models.ForeignKey("Requete", on_delete=models.CASCADE)
    resid = models.IntegerField(default=-1)
    poid = models.FloatField(default=0.)
    distance = models.FloatField(null=True, blank=True)

    def get_ressource(self):
        return Ressource.objects.get(resid=self.resid)
