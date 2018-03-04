from treetaggerwrapper import TreeTagger
import numpy as np
from scipy.spatial.distance import cosine
from juridico_site.settings import BASE_DIR
from collections import Counter
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

vec = np.load(BASE_DIR+"/juridico/vecteurs_juridico.npz")
mots = list(vec["mots"])

def str2date(s):
    d,m,y = tuple(int(i) for i in re.split("[/-. ]+", self.reponse.strip()))
    return date(y,m,d)

def date2str(d):
    return d.strftime("%d/%M/%Y")

def rd_gt(r1, r2):
    """Compare deux relativedeltas, détermine si le premier est plus grand que
    le deuxième."""
    for m in ("years", "months", "days"):
        if getattr(r1, m) > getattr(r2, m):
            return True
        elif getattr(r1, m) < getattr(r2, m):
            return False

    # If they're actually equal:
    return False

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

def get_valeur(requete, nom):
    return Variable.objects.get(nom=nom).vale

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
        # Appartient au domaine familial
        return 9

def question3(requete, reponse):
    # À quelle date avez-vous reçu ce document?
    stocker_valeur(requete, "date_reception", reponse.reponse)

    if r == "Avis d'augmentation de loyer et de modification d'une autre condition du bail":
        return 4
    elif r in ("Avis de reprise de logement", "Avis de réparation ou amélioration majeure"):
        return 5

def stockage_q45_jesaispas(requete):
    add_direction(requete, "Selon les informations fournies, nous ne pouvons pas calculer si l’avis que votre propriétaire vous a envoyé respecte les délais. Pour déterminer cela, vous pouvez amener les papiers suivants : 1. Bail écrit ; 2. Avis de modification de bail , au comité logement le plus proche de chez vous, qui vous répondront gratuitement.")
    add_direction("""Lorsque l’avis respecte les délais,
    <ul>
        <li>Vous pouvez communiquer votre refus ou votre acceptation de la modification. Si vous ne répondez pas à l’avis, cela équivaudra à une acceptation des modifications. </li>
        <li>Si vous acceptez la modification, celle-ci prendra effet au terme de la durée du bail qui sera donc reconduit suivant les nouvelles modalités acceptées. </li>
        <li>Si vous refusez la modification, votre bail est tout de même reconduit et vous garder votre logement. </br>
        À ce moment-vous pouvez :</li>
        <ul>
            <li>Essayer de vous entendre avec votre propriétaire pour une hausse que vous seriez capable d’accepter </li>
            <li>Ne rien faire. Et dans ce cas, il est possible que votre propriétaire laisse tomber, comme il est possible qu’il s’adresse à la Régie du logement s’il souhaite quand même augmenter le loyer.  </li>
            <li>Si le propriétaire ne va pas à la Régie du logement, votre bail sera reconduit aux mêmes conditions (et donc sans la hausse proposée par votre propriétaire dans l’avis).  <li>
            <li>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu.<li>
        </ul>
    </ul>""")

def question4(requete, reponse):
    # Quelle est la durée de votre bail?
    # Pour un avis d'augmentation de loyer
    stocker_valeur(requete, "durée_bail", reponse.reponse)

    if reponse.reponse == "Bail de 12 mois et plus":
        return 6
    elif reponse.reponse == "Bail de moins de 12 mois":
        return 6
    elif reponse.reponse == "Bail à durée indéterminée":
        return 7
    elif reponse.reponse == "Je ne sais pas":
        stockage_q45_jesaispas(requete)
        return -1 # Terminé le parcours

def question5(requete, reponse):
    # Quelle est la durée de votre bail?
    # Pour un avis d'augmentation de loyer
    stocker_valeur(requete, "durée_bail", reponse.reponse)

    if reponse.reponse == "Bail de 12 mois et plus":
        return 18
    elif reponse.reponse == "Bail de moins de 12 mois":
        return 18
    elif reponse.reponse == "Bail à durée indéterminée":
        return 18
    elif reponse.reponse == "Je ne sais pas":
        # stockage_q45_jesaispas(requete)
        # Honnêtement, je sais pas trop quoi faire ici...
        return 18

def question6(requete,reponse):
    # Quelle est la date de fin de bail?
    stocker_valeur(requete, "date_fin_de_bail", reponse.reponse)
    duree_bail = get_valeur(requete, "durée_bail")
    fin_bail = str2str2date(reponse.reponse)
    date_reception = str2str2date(get_valeur(requete, "date_reception"))

    dmois_reception_fin_bail = relativedelta(fin_bail, date_reception)
    d6mois = relativedelta(months=6)
    d3mois = relativedelta(months=3)

    if duree_bail == "Bail de 12 mois et plus" and \
        rd_gt(d6mois,dmois_reception_fin_bail) and \
        not rd_gt(d3mois, dmois_reception_fin_bail): #équivaut à ≥ 3 mois & < 6 mois

        add_direction("Selon l'information que vous nous avez fourni, l'avis de votre propriétaire respecte les délais (envoyé entre 3 et 6 mois avant la fin du bail).")

        date_limite_reponse = date_reception + timedelta(months=1)
