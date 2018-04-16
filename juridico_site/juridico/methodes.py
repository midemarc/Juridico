import re
from treetaggerwrapper import TreeTagger
import numpy as np
from scipy.spatial.distance import cosine, cdist
from juridico_site.settings import BASE_DIR
from collections import Counter
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from .models import *
#import locale
from .models import Variable, RessourceDeRequete, Direction, Documentation, Organisation
from gensim.models import Doc2Vec
import pickle
import re
from geopy.distance import vincenty
from django.db.models import Q
from datetime import datetime
import os

vec = np.load(BASE_DIR+"/juridico/vecteurs_juridico.npz")
mots = list(vec["mots"])
d2v = Doc2Vec.load(BASE_DIR+"/educaloi_cappel_d2v.model")
#locale.setlocale(locale.LC_ALL, "fr_CA.utf-8")

cp_codes, cp_pts = tuple(zip(*pickle.load(open(BASE_DIR+"/codes_postaux.pickle", 'rb'))))
cp_dict = dict(zip(cp_codes,cp_pts))

from geoip2.database import Reader as georeader_mk
from geoip2.errors import AddressNotFoundError
georeader = georeader_mk(BASE_DIR+"/GeoLite2-City.mmdb")


mois_fr = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
mois_en = "January February March April May June July August September October November December".split()

# Types de formattages de date
# datet2 correspond au type de l'interface angular/ts, datet2 au type de l'interface django
datet1 = re.compile(r"(?P<an>[0-9]{4})-(?P<mois>[0-9]{2})-(?P<jour>[0-9]{2})T[0-9]{2}:[0-9]{2}:[0-9]{2}[.][0-9]{3}Z")
datet2 = re.compile(r"(?P<jour>[0-9]{2})[-/](?P<mois>[0-9]{2})[-/](?P<an>[0-9]{4})")

def str2date(s):
    "Convertit une date formattée dans une chaîne en date python"
    m = datet1.match(s)
    if s == None: m = datet2.match(s)
    return date(
        int(m.group("an")),
        int(m.group("mois")),
        int(m.group("jour"))
    )

def date2str(d):
    "Convertit une date python vers une chaîne au format de date standard pour Juridico"
    return d.strftime("%d/%M/%Y")

def formatter_date(d, lang="fr"):
    "Convertit une date python vers une chaîne contenant une date lisible en français."
    if lang == "fr":
        mois = mois_fr[d.month-1]
    elif lang == "en":
        mois = mois_en[d.month-1]
    return d.strftime("%-d {mois} %Y").format(mois=mois)

def cp2geo(cp):
    "À partir du code postal canayen, retourne des coordonnées geo"
    r = cp_dict.get(re.sub("[^A-Z0-9]","",cp.upper()), None)
    if r == None:
        return None
    else:
        return (r[1], r[0])

def switch_geo(pt):
    "Bizzarement, mes coordonnées sont à l'envers (longitude,latitude). Ça les remet à l'endroit."
    return (pt[1], pt[0])

def plus_proche_org(lat, long, conditions=None, max_km=100):
    """Retourne les topn plus proches organisations.
    conditions: sous la forme dict où la clé est un nom de TagType et la valeur
    est un nom de tag. Si ce n'est pas None, alors ne cherche que parmis les
    objets qui ont le tag correspondant du type de tag correspondant."""
    #TODO: se donner un plan pour comment sortir les org qui ont pas de coordonnées (e.g. sur appel)

    if conditions == None:
        pool = Organisation.objects.all()
    else:
        pool = Organisation.objects
        for k, v in conditions.items():
            pool = pool.filter(tags__nom=v, tags__type_de_tag__nom=k)

    if pool.count() == 0: return []

    r = [ (o.coords2dist(lat,long), o.resid) for o in pool ]
    x = [ (None, o) for d,o in r if d==None ]
    r = list(sorted((d, o) for d, o in r if d != None), )
    for d, o in  r + x:
        yield (d, Organisation.objects.get(resid=o))

def rd_gt(r1, r2):
    """Compare deux relativedeltas, détermine si le premier est plus grand que
    le deuxième."""
    for m in ("years", "months", "days"):
        if getattr(r1, m) > getattr(r2, m):
            return True
        elif getattr(r1, m) < getattr(r2, m):
            return False

def rd_gte(r1, r2):
    """Compare deux relativedeltas, détermine si le premier est plus grand
    ou égal au deuxième."""
    for m in ("years", "months", "days"):
        if getattr(r1, m) < getattr(r2, m):
            return False
    return True

    # If they're actually equal:
    return False

def text2vec(description_cas):
    "Convertit du texte en vecteur sur l'espace du modèle Doc2Vec d2v"

    ttroot = os.path.abspath(os.path.join(os.getcwd(), "treetagger-install"))

    tagger = TreeTagger(TAGLANG="fr", TAGDIR=ttroot)
    t = [ ln.split("\t") for ln in tagger.tag_text(description_cas.lower()) ]
    t = [ i[2] for i in t if len(i)==3 ]
    t = [ i for i in t for i in d2v.wv.index2entity ]

    return d2v.infer_vector(t)

def desc2domaine(description_cas, dom_logement=1, dom_famille=9):
    """Classifieur: détermine si la description appartient au droit de la
    famille ou au droit du logement.
    TODO: remplacer par une fonction qui utilise les doc2vec (je fais pas trop
    confiance au nearest neighbor — c'est presque toujours le pire classifieur)
    """

    ttroot = os.path.abspath(os.path.join(os.getcwd(), "treetagger-install"))

    tagger = TreeTagger(
        TAGLANG="fr",
        TAGDIR=ttroot
    )
    v = np.zeros(len(mots))
    t = [ ln.split("\t") for ln in tagger.tag_text(description_cas) ]
    t = [ i[2] for i in t if len(i)==3 ]
    t = [ i for i in t for i in mots ]

    nmots = float(len(t))

    for k, val in Counter(t).items():
        v[mots.index(k)] = val / nmots

    dfamille = cosine(v, vec["famille"])
    dlogement = cosine(v, vec["logement"])

    if dlogement < dfamille:
        return dom_logement
    else:
        return dom_famille

def get_top_educaloi(v, topn=10):
    """Renvoie les pages educaloi les plus similaires au vecteur soumis"""

    is_el = re.compile("^EL_")
    idx_educaloi = np.nonzero(np.fromiter((is_el.match(i) !=None for i in d2v.docvecs.index2entity), dtype=bool))[0]
    distances = cdist([v], d2v.docvecs.vectors_docs[idx_educaloi], metric="cosine")[0]
    return list(sorted(zip(distances, (Documentation.objects.get(artid_educaloi=int(d2v.docvecs.index2entity[i][3:])) for i in idx_educaloi))))[:topn]

def add_ressource(requete, ressource, poids=1.0, typ="", distance=None):
    "Ajoute une ressource à la liste des résultats"

    q, _ = RessourceDeRequete.objects.update_or_create(
        requete=requete,
        resid=ressource.resid,
        defaults = {
            "poids": poids,
            "type_classe": typ,
            "distance": distance
        }
    )
    q.save()

def add_documentation(requete,resid, poids=1.0):
    add_ressource(requete, Documentation.objects.get(resid=resid), typ="Documentation", poids=poids)

def add_direction(requete,resid, poids=1.0):
    add_ressource(requete, Direction.objects.get(resid=resid), typ="Direction", poids=poids)

def add_organisation(requete,resid, distance=None, poids=1.0):
    add_ressource(requete, Organisation.objects.get(resid=resid), typ="Organisation", distance=distance, poids=poids)

def add_orgs(requete, conditions, topn=10, poids=1.0):
    lat = requete.client.latitude
    long = requete.client.longitude

    if lat == None or long == None:
        if requete.client.get_code_postal() != None:
            if requete.client.get_code_postal() in cp_codes:
                long, lat = cp_dict[requete.client.get_code_postal()]

        if long == None or lat == None:
            try:
                loc = georeader.city(requete.ip).location
                lat = loc.latitude
                long = loc.longitude
            except AddressNotFoundError:
                lat, long = (45.513889, -73.560278)

    for d, o in tuple(plus_proche_org(lat, long, conditions))[:topn]:
        add_ressource(requete, o, poids=poids, distance=d, typ="Organisation")

def add_client(requete, client, poids=1.0):
    d = Organisation.objects.get(client=client)
    if d == None:
        d = Organisation.objects.create(
            description = "",
            client=client
        )
        d.save()
    r2r = RessourceDeRequete.objects.create(
        requete = requete,
        resid = d.resid,
        poids = poids
    )
    r2r.save()

def stocker_valeur(requete, nom, val):
    v, _ = Variable.objects.update_or_create(
        nom=nom,
        requete=requete,
        defaults = {"valeur": val}
    )
    v.save()

def get_valeur(requete, nom, default=None):
    v = Variable.objects.get(nom=nom, requete=requete)
    return v.valeur if v != None else default

#################
# Les Questions #
#################

def question1(requete, reponse):
    if reponse.reponse.strip().lower() == "oui":
        return 2
    else:
        return -1

def question2(requete, reponse):
    r = reponse.reponse
    stocker_valeur(requete, "document_reçu", r)
    if r == "Avis d'augmentation de loyer et de modification d'une autre condition du bail":
        add_direction(requete,1)
        add_documentation(requete, 219)
        return 3
    elif r == "Avis de reprise de logement":
        add_direction(requete, 2)
        add_documentation(requete, 223)
        return 3
    elif r == "Avis de réparation ou amélioration majeure":
        add_direction(requete, 3)
        add_documentation(requete,363) # Informations sur les réparations majeures en logement
        return 3
    elif r == "Demande introductive d’instance":
        # Appartient au domaine familial
        return 9
    else:
        return -1 # Pour les cas non-traités...


def question3(requete: Requete, reponse: Reponse):
    # À quelle date avez-vous reçu ce document?
    stocker_valeur(requete, "date_reception", reponse.reponse)

    document_recu = get_valeur(requete, "document_reçu")

    if document_recu == "Avis d'augmentation de loyer et de modification d'une autre condition du bail":
        return 4
    elif document_recu == "Avis de reprise de logement":
        return 5
    elif document_recu == "Avis de réparation ou amélioration majeure":
        return 23
    else:
        return -1

def question4(requete, reponse):
    # Quelle est la durée de votre bail?
    # Pour un avis d'augmentation/modif de loyer
    stocker_valeur(requete, "durée_bail", reponse.reponse)

    if reponse.reponse == "Bail de 12 mois et plus":
        return 6
    elif reponse.reponse == "Bail de moins de 12 mois":
        return 6
    elif reponse.reponse == "Bail à durée indéterminée":
        return 7
    elif reponse.reponse == "Je ne sais pas":
        add_direction(requete, 4)
        add_direction(requete, 5)
        return -1 # Terminé le parcours

def question5(requete, reponse):
    # Quelle est la durée de votre bail?
    # Reprise de logement, travaux majeurs
    stocker_valeur(requete, "durée_bail", reponse.reponse)

    if reponse.reponse == "Bail de 6 mois et plus":
        return 18
    elif reponse.reponse == "Bail de moins de 6 mois":
        return 18
    elif reponse.reponse == "Bail à durée indéterminée":
        return 19
    elif reponse.reponse == "Je ne sais pas":
        add_direction(requete, 6)
        add_direction(requete, 7)

        add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Comité Logement"}, topn=5)
        add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Avocat·e"}, topn=5)
        return -1


def question6(requete,reponse):
    # Quelle est la date de fin de bail?
    stocker_valeur(requete, "date_fin_de_bail", reponse.reponse)
    duree_bail = get_valeur(requete, "durée_bail")
    fin_bail: datetime = str2date(reponse.reponse)
    date_reception: datetime = str2date(get_valeur(requete, "date_reception"))

    dmois_reception_fin_bail = relativedelta(fin_bail, date_reception)
    d6mois = relativedelta(months=6)
    d3mois = relativedelta(months=3)
    d1mois = relativedelta(months=1)
    d2mois = relativedelta(months=2)

    if duree_bail == "Bail de 12 mois et plus" and \
        rd_gt(d6mois,dmois_reception_fin_bail) and \
        not rd_gt(d3mois, dmois_reception_fin_bail): #équivaut à ≥ 3 mois & < 6 mois

        add_direction(requete, 8)

        date_limite_reponse = date_reception + relativedelta(months=1)
        njours = (date_limite_reponse-date.today()).days

        stocker_valeur(requete, "q6_date_limite_reponse", formatter_date(date_limite_reponse))
        stocker_valeur(requete, "q6_njours", njours)

        add_direction(requete, 9)

    elif duree_bail == "Bail de 12 mois et plus" and \
        (not rd_gt(d6mois,dmois_reception_fin_bail) or \
        rd_gt(d3mois, dmois_reception_fin_bail)):

        add_direction(requete, 10)

    elif duree_bail == "Bail de moins de 12 mois" and \
        rd_gt(d2mois,dmois_reception_fin_bail) and \
        not rd_gt(d1mois, dmois_reception_fin_bail):

        add_direction(requete, 8)

        date_limite_reponse = date_reception + relativedelta(months=1)
        njours = (date_limite_reponse-date.today()).days

        stocker_valeur(requete, "q6_date_limite_reponse", formatter_date(date_limite_reponse))
        stocker_valeur(requete, "q6_njours", njours)

        add_direction(requete, 11)

    elif duree_bail == "Bail de moins de 12 mois" and \
        (not rd_gt(d2mois,dmois_reception_fin_bail) or \
        rd_gt(d1mois, dmois_reception_fin_bail)):

        add_direction(requete,10)

    return -1

def question7(requete, reponse):
    stocker_valeur(requete, "date_de_modification_souhaitée", reponse.reponse)
    date_modifs = str2date(reponse.reponse)
    date_reception = str2date(get_valeur(requete, "date_reception"))

    dmois_reception_modifs = relativedelta(date_modifs, date_reception)
    d1mois = relativedelta(months=1)
    d2mois = relativedelta(months=2)

    if rd_gt(d1mois,dmois_reception_modifs) and \
        not rd_gt(d2mois, dmois_reception_modifs): #équivaut à ≥ 3 mois & < 6 mois

        add_direction(8)

        date_limite_reponse = date_reception + relativedelta(months=1)
        njours = (date_limite_reponse-date.today()).days

        stocker_valeur(requete, "q6_date_limite_reponse", formatter_date(date_limite_reponse))
        stocker_valeur(requete, "q6_njours", njours)

        add_direction(requete, 11)

    else:

        add_direction(requete, 10)

    return -1

def question18(requete,reponse):
    stocker_valeur(requete, "date_fin_de_bail", reponse.reponse)
    duree_bail = get_valeur(requete, "durée_bail")
    fin_bail = str2date(reponse.reponse)
    date_reception = str2date(get_valeur(requete, "date_reception"))

    dmois_reception_fin_bail = relativedelta(fin_bail, date_reception)
    d6mois = relativedelta(months=6)
    d1mois = relativedelta(months=1)

    if duree_bail == "Bail de 6 mois et plus":
        if rd_gte(dmois_reception_fin_bail, d6mois):

            add_direction(requete, 12)

            date_limite_reponse = date_reception + relativedelta(months=1)
            njours = (date_limite_reponse-date.today()).days

            stocker_valeur(requete, "q18_date_limite_reponse", formatter_date(date_limite_reponse))
            stocker_valeur(requete, "q18_njours", njours)

            add_direction(requete, 13)

            add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Comité Logement"}, topn=5)
            add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Avocat·e"}, topn=5)

        else:
            add_direction(requete, 10)
    elif duree_bail == "Bail de moins de 6 mois":
        if rd_gte(dmois_reception_fin_bail, d1mois):

            add_direction(requete, 14)

            date_limite_reponse = date_reception + relativedelta(months=1)
            njours = (date_limite_reponse-date.today()).days

            stocker_valeur(requete, "q18_date_limite_reponse", formatter_date(date_limite_reponse))
            stocker_valeur(requete, "q18_njours", njours)

            add_direction(requete, 15)

            add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Comité Logement"}, topn=5)
            add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Avocat·e"}, topn=5)

        else:
            add_direction(requete, 10)
    return -1

def question19(requete,reponse):
    stocker_valeur(requete, "date_reprise_des_lieux", reponse.reponse)
    date_reprise_des_lieux = str2date(reponse.reponse)
    date_reception = str2date(get_valeur(requete, "date_reception"))

    dmois_reception_reprise = relativedelta(date_reprise_des_lieux, date_reception)
    d6mois = relativedelta(months=6)

    if rd_gte(dmois_reception_reprise, d6mois):

        add_direction(requete, 12)

        date_limite_reponse = date_reception + relativedelta(months=1)
        njours = (date_limite_reponse-date.today()).days

        stocker_valeur(requete, "q19_date_limite_reponse", formatter_date(date_limite_reponse))
        stocker_valeur(requete, "q19_njours", njours)

        add_direction(requete, 16)

        add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Comité Logement"}, topn=5)
        add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Avocat·e"}, topn=5)

    else:
        add_direction(requete, 10)

    return -1

def question23(requete,reponse):
    # Date de début des travaux
    stocker_valeur(requete,"date_debut_travaux", reponse.reponse)

    date_reception = str2date(get_valeur(requete, "date_reception"))
    date_debut_travaux = str2date(reponse.reponse)

    return 24

def question24(requete,reponse):
    # Évacué pour plus d'une semaine?
    date_reception = str2date(get_valeur(requete, "date_reception"))
    date_debut_travaux = str2date(get_valeur(requete, "date_debut_travaux"))
    njours = (date_debut_travaux-date_reception).days
    d_reception_debut_travaux = relativedelta(date_debut_travaux,date_reception)
    rep = reponse.reponse.strip().lower()
    d3mois = relativedelta(months=3)

    if rep == "non":
        if njours < 10:
            add_direction(requete, 17)
        else:
            add_direction(requete, 18)
            date_max = date_reception + timedelta(days=10)
            stocker_valeur(requete, "date_max", formatter_date(date_max))

            add_direction(requete, 19)

            add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Comité Logement"}, topn=5)
            add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Avocat·e"}, topn=5)

    if rep == "oui":
        if rd_gt(d3mois, d_reception_debut_travaux):
            add_direction(requete, 20)
        else:
            add_direction(requete, 21)
            date_max = date_reception + timedelta(days=10)
            stocker_valeur(requete, "date_max", formatter_date(date_max))

            add_direction(requete, 19)

            add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Comité Logement"}, topn=5)
            add_orgs(requete, {"Spécialité":"Droit du logement", "Type de ressource": "Avocat·e"}, topn=5)
    return -1

# Questions de Stéfanny

def question9(requete,reponse):
    stocker_valeur(requete,"demande_en_divorce", reponse.reponse)
    return 10

def question10(requete,reponse):
    stocker_valeur(requete,"enfants_mineurs", reponse.reponse)
    return 11

def question11(requete,reponse):
    stocker_valeur(requete,"propriété_en_commun", reponse.reponse)
    return 12

def question12(requete,reponse):
    stocker_valeur(requete,"ouvert_a_mediation", reponse.reponse)
    return 13

def question13(requete,reponse):
    stocker_valeur(requete,"date_reception", reponse.reponse)
    return 14

def question14(requete,reponse):
    if reponse.reponse.strip().lower() == "non":
        return -1
    else:
        return 15

def question15(requete,reponse):
    stocker_valeur(requete,"date_avis_presentation", reponse.reponse)
    return 16

def question16(requete,reponse):
    stocker_valeur(requete,"autorepresentation", reponse.reponse)
    return 17

def question17(requete,reponse):
    stocker_valeur(requete,"admissible_aide_juridique", reponse.reponse)

    F1 = get_valeur(requete, "demande_en_divorce")
    F2 = get_valeur(requete,"enfants_mineurs")
    F8 = get_valeur(requete, "autorepresentation")
    F5 = str2date(get_valeur(requete,"date_reception"))
    F7 = str2date(get_valeur(requete,"date_avis_presentation"))
    F9 = reponse.reponse.strip().lower()

    if F8 == "oui":
        if F1.lower().strip() == "non":
            stocker_valeur(requete, "q17_date_cour", formatter_date(F7))
            add_direction(requete, 23)
        else:
            add_direction(requete, 22)
    if F2.lower().strip() == "oui":
        add_direction(requete, 24)
    return -1
