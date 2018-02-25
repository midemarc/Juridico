from treetaggerwrapper import TreeTagger
import numpy as np
from scipy.spatial.distance import cosine
from juridico_site.settings import BASE_DIR
from collections import Counter

vec = np.load(BASE_DIR+"/juridico/vecteurs_juridico.npz")
mots = list(vec["mots"])

def desc2domaine(description_cas, dom_logement=1, dom_famille=2):
    tagger = TreeTagger(TAGLANG="fr")
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

def add_direction(requete, texte, quand):
    d = Direction.objects.create(
        description = texte,
        quand = quand
    )
    d.save()
    r2r = RessourceDeRequete.objects.create(
        requete = requete,
        resid = d.resid,
        poid = 1.
    )
    r2r.save()

def add_organisation(requete, nom, desc, url):
    d = Organisation.objects.create(
        description = desc,
        url = url,
        nom = nom
    )
    d.save()
    r2r = RessourceDeRequete.objects.create(
        requete = requete,
        resid = d.resid,
        poid = 1.
    )

def add_documentation(requete, nom, url):
    d = Organisation.objects.create(
        description = desc,
        url = url,
        nom = nom
    )
    d.save()
    r2r = RessourceDeRequete.objects.create(
        requete = requete,
        resid = d.resid,
        poid = 1.
    )

def add_camarade(requete, client):
    d = Organisation.objects.create(
        description = "",
        client=client
    )
    d.save()
    r2r = RessourceDeRequete.objects.create(
        requete = requete,
        resid = d.resid,
        poid = 1.
    )

def question1(requete, reponse):
    if reponse.reponse.lower() == "oui":
        return 2
    else:
        return None # À changer

def question2(requete, reponse):
    r = reponse.reponse
    if r == "Avis d'augmentation de loyer et de modification d'une autre condition du bail":
        add_direction(requete,"Vous avez reçu un “Avis d'augmentation de loyer et de modification d'une autre condition du bail”. Cet avis est nécessaire lorsque votre propriétaire veut modifier les conditions de votre bail, telle que le montant du loyer.","[Info]")
