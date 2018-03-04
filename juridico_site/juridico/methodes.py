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
    r2r.save()

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
    r2r.save()

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
    r2r.save()

def stocker_valeur(requete, nom, val):
    v = Variable.objects.create(
        nom=nom,
        requete=requete,
        valeur=val
    )
    v.save

get_valeur()

def question1(requete, reponse):
    if reponse.reponse.lower() == "oui":
        return 2
    else:
        return None # À changer

def question2(requete, reponse):
    r = reponse.reponse
    stocker_valeur(requete, "document_reçu", r)
    if r == "Avis d'augmentation de loyer et de modification d'une autre condition du bail":
        add_direction(requete,"Vous avez reçu un “Avis d'augmentation de loyer et de modification d'une autre condition du bail”. Cet avis est nécessaire lorsque votre propriétaire veut modifier les conditions de votre bail, telle que le montant du loyer.","[Info]")
        add_documentation(requete, "Informations sur le renouvellement de bail et les augmentations de loyer", "https://www.educaloi.qc.ca/capsules/le-renouvellement-de-bail-et-la-hausse-de-loyer")
        return 3
    elif r == "Avis de reprise de logement":
        add_direction(requete, "Vous avez reçu un avis de reprise de logement. Votre propriétaire doit vous faire parvenir un tel avis écrit pour vous informer de son intention de reprendre le logement pour lui-même ou pour un membre de sa famille (soit ses enfants, ses parents ou une personne directement à sa charge).")
        add_documentation(requete, "Informations sur la reprise de logement", "https://www.educaloi.qc.ca/capsules/la-reprise-du-logement-et-leviction")
    elif r == "Avis de réparation ou amélioration majeure":
        add_direction(requete, "Vous avez reçu un “Avis de réparation ou amélioration majeure”. Cet avis est nécessaire lorsque le propriétaire souhaite apporter des améliorations ou de faire des réparations majeures touchant votre logement.")
        add_documentation("Informations sur les réparations majeures en logement", "https://www.rdl.gouv.qc.ca/fr/le-logement/travaux-majeurs")
    elif r == "Demande introductive d’instance":
        # Appartient au domaine familial... les questions ne sont pas encore entrées
        pass

def question3(requete, reponse):
    stocker_valeur(requete, reponse.reponse)

    if r == "Avis d'augmentation de loyer et de modification d'une autre condition du bail":
        return 4
    elif r in ("Avis de reprise de logement", "Avis de réparation ou amélioration majeure"):
        return 5
