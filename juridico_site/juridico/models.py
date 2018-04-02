from django.db import models
from datetime import datetime, timedelta, date
import re
from geopy.distance import vincenty
from django.core.validators import RegexValidator

# Create your models here.

item_html = """<div class="item{extra_class}">
<h4><a href="{url}">{titre}</a></h4>
<div class="description"></div>
</div>"""


def formfield2html(typ, name, value=None, choix=[], disabled=False):
    dis = " disabled" if disabled else ""
    if typ == "t":
        val = value if value else ""
        r = f'<textarea name="{name}" rows="8" cols="80"{dis}>{val}</textarea>'
    elif typ == "e":
        val = value if value else 0
        r = f'<input type="number" name="{name}" value="{val}"{dis}>'
    elif typ == "f":
        val = value if value else 0
        r = f'<input type="text" name="{name}" value="{val}"{dis}>'
    elif typ == "b":
        val = value if value else False
        if val:
            opt = '<option value="oui" selected>Oui</option><option value="non">Non</option>'
        else:
            opt = '<option value="oui">Oui</option><option value="non" selected>Non</option>'
        r = f'<select name="{name}"{dis}>{opt}</select>'
    elif typ == "d":
        did =  ' id="datepicker"' if not disabled else ""
        val = ' value="%s"' % value.strftime("%a %b %d %Y") if isinstance(value, date) else ""
        # r = f'<input type="text"  class="ui calendar""{val}{did}>'
        r = f"""<div class="ui calendar"{did}>
    <div class="ui input left icon">
      <i class="calendar icon"></i>
      <input type="text" placeholder="Date" name="{name}" {val}{did}>
  </div>
</div>"""

    elif typ == "l":
        val = value if value else choix[0]
        opt = ""
        for c in choix:
            sel = " selected" if c.strip().lower() == val.strip().lower() else ""
            opt+= f'\n<option value="{c}"{sel}>{c}</option>'
        r = f'<select name="{name}"{dis}>{opt}</select>'
    return r


class Tag(models.Model):
    tid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=256, help_text="Nom du tag (français)")
    nom_en = models.CharField(max_length=256, help_text="Nom du tag (anglais)", blank=True)
    type_de_tag = models.ForeignKey("TagType", blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.type_de_tag ==None:
            return "(%d) %s" % (self.tid,self.nom)
        else:
            return "(%d) %s → %s" % (self.tid,self.type_de_tag.nom, self.nom)


class TagType(models.Model):
    ttid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=256, help_text="Nom du type de tag (français)")
    nom_en = models.CharField(max_length=256, help_text="Nom du type de tag (anglais)", blank=True)
    def __str__(self):
        return "(%d) %s" % (self.ttid,self.nom)

class Client(models.Model):
    pseudo = models.CharField(max_length=128, unique=True)
    cid = models.AutoField(primary_key=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modif = models.DateTimeField(auto_now=True)
    courriel = models.EmailField()
    tags = models.ManyToManyField("Tag", blank=True)
    langue = models.CharField(
        choices = (
            ("fr", "français"),
            ("en", "english")
        )
    ,max_length=2, blank=True) # Pour le moment, on n'a que deux langues...
    #TODO: Possibilité d'en ajouter d'autres
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    code_postal = models.CharField(
        max_length=7,
        blank=True,
        help_text = "Sert à géolocaliser.",
        validators = [RegexValidator(
            regex = r"^[A-Z][0-9][A-Z] ?[0-9][A-Z][0-9]$",
            message = "Format invalide pour un code postal. Le format est: X0X 0X0, où X est une lettre et 0 un chiffre."
        )]
    )
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
    question = models.TextField(help_text="Question posée à l'usager·e (français).")
    question_en = models.TextField(help_text="Question posée à l'usager·e (anglais).", blank=True)
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

    def get_html(self):
        return formfield2html(
            typ=self.reponse_type,
            name="reponse",
            choix=self.contenu_liste.split("\n"),
            disabled=False
        )


class Categorie(models.Model):
    # Les catégories concernent le contenu, là où les Tags concernent des
    # attributs divers (spécialité, langue, etc.) utiles pour l'usager·e
    catid = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=1024, help_text="Nom de la catégorie (français)")
    nom_en = models.CharField(max_length=1024, help_text="Nom de la catégorie (anglais)", blank=True)
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
        r = self.question.reponse_type
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
            from juridico.methodes import str2date
            return str2date(self.reponse.strip())

    def get_html(self):
        return formfield2html(
            typ=self.question.reponse_type,
            name="rep_old_%d" % self.repid,
            value=self.get_value(),
            choix=self.question.contenu_liste.split("\n"),
            disabled=True
        )

class Requete(models.Model):
    reqid = models.AutoField(primary_key=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modif = models.DateTimeField(auto_now=True)
    ip = models.CharField(max_length=64, default="132.208.170.58")

    description_cas = models.TextField()
    description_vec = None
    client = models.ForeignKey("Client", on_delete=models.CASCADE)

    def get_desc_vector(self):
        from juridico.methodes import text2vec
        if self.description_vec == None:
            self.description_vec = text2vec(self.description_cas)
        return self.description_vec

    def get_requete_educaloi(self, topn=10):
        return [i[1] for i in get_top_educaloi(self.get_desc_vector(), topn=topn)]


# Types de ressources

class Ressource(models.Model):
    resid = models.AutoField(primary_key=True, unique=True)
    description = models.TextField(blank=True, help_text="Description de la ressource (français)")
    description_en = models.TextField(blank=True, help_text="Description de la ressource (anglais)")
    tags = models.ManyToManyField("Tag", blank=True)
    commentaires = models.TextField(blank=True)
    type_classe = models.CharField(max_length=32, default="", blank=True)

    class Meta:
        abstract = True

class Organisation(Ressource):
    nom = models.CharField(max_length=256, help_text="Nom de l'organisme (français)")
    nom_en = models.CharField(max_length=256, help_text="Nom de l'organisme (anglais)", blank=True)
    url = models.CharField(max_length=1024, blank=True, help_text="URL de l'organisme (français)")
    url_en = models.CharField(max_length=1024, blank=True, help_text="URL de l'organisme (anglais)")
    code_postal = models.CharField(
        max_length=7,
        blank=True,
        help_text = "Sert à géolocaliser.",
        validators = [RegexValidator(
            regex = r"^[A-Z][0-9][A-Z] ?[0-9][A-Z][0-9]$",
            message = "Format invalide pour un code postal. Le format est: X0X 0X0, où X est une lettre et 0 un chiffre."
        )]
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
    appartenance_en = models.CharField(
        max_length=1024,
        blank=True,
        help_text = "Par exemple, pour un·e avocat·e ou notaire, son cabinet."
    )
    telephone = models.CharField(max_length=64, blank=True)
    telecopieur = models.CharField(max_length=64, blank=True)
    heures_ouverture = models.TextField(blank=True)
    heures_ouverture_en = models.TextField(blank=True)

    def __str__(self):
        return f"({self.resid}) {self.nom}"

    def get_cp(self):
        "Retourne le code postal, format X0X0X0."
        return re.sub("\s+", "", self.code_postal.upper())

    def to_resultats(self):
        return item_html.format(
            url=self.url,
            titre=self.nom,
            description=self.description,
            extra_class=" organisation"
        )

    def coords2dist(self, lat, long):
        "En km."
        if self.latitude == None or long == None:
            return None
        else:
            return vincenty((self.latitude,self.longitude),(lat,long)).km

class Documentation(Ressource):
    nom = models.CharField(max_length=256, help_text="Nom du document (français)")
    url = models.CharField(max_length=102, help_text="URL du document (français)")
    nom_en = models.CharField(max_length=256, help_text="Nom du document (anglais)", blank=True)
    url_en = models.CharField(max_length=1024, help_text="URL du document (anglais)", blank=True)
    artid_educaloi = models.IntegerField(blank=True, null=True)
    categorie_educaloi = models.CharField(max_length=256, blank=True, null=True)
    categorie_educaloi_en = models.CharField(max_length=256, blank=True, null=True)
    nom_source = models.ForeignKey("DocuSource", blank=True, null=True, on_delete=models.SET_NULL)

    def to_resultats(self):
        return item_html.format(
            url=self.url,
            titre=self.nom,
            description=self.description,
            extra_class=" documentation"
        )

    def source(self):
        return self.nom_source.nom

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
    nom = models.CharField(max_length=256, help_text="Nom de la source (français)")
    nom_en = models.CharField(max_length=256, help_text="Nom de la source (anglais)", blank=True)
    url = models.CharField(max_length=1024, blank=True, null=True, help_text="Nom de la source (français)")
    url_en = models.CharField(max_length=1024, blank=True, null=True, help_text="Nom de la source (anglais)")

    def __str__(self):
        return "(%d) %s" % (self.dcid, self.nom)

class Camarade(Ressource):
    client = models.ForeignKey("Client", on_delete=models.CASCADE)
    code_postal = models.CharField(
        max_length=7,
        blank=True,
        help_text = "Sert à géolocaliser.",
        validators = [RegexValidator(
            regex = r"^[A-Z][0-9][A-Z] ?[0-9][A-Z][0-9]$",
            message = "Format invalide pour un code postal. Le format est: X0X 0X0, où X est une lettre et 0 un chiffre."
        )]
    )

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

    def formatted_description(self, requete):
        "Donne la description formattée avec les variables pertinentes."
        if self.variables != "":
            from juridico.methodes import get_valeur
            vs = self.variables.split()
            d = dict(
                (v, get_valeur(requete, v, "")) for v in vs
                if "{%s}" %v in self.description
            )
            desc = self.description.format(**d)
        else:
            desc = self.description
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
    poids = models.FloatField(default=0.)
    distance = models.FloatField(null=True, blank=True)
    type_classe = models.CharField(max_length=32, default="", blank=True)

    def get_ressource(self):
        if self.type_classe == "Documentation":
            return Documentation.objects.get(resid=self.resid)
        elif self.type_classe == "Organisation":
            return Organisation.objects.get(resid=self.resid)
        elif self.type_classe == "Direction":
            return Direction.objects.get(resid=self.resid)

    def __str__(self):
        reqid = self.requete.reqid
        res = self.get_ressource()
        desc=res.description if res != None else ""
        typ =  self.type_classe
        return f"[{reqid}] {typ}: {desc}"
