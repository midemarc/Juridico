import re
from treetaggerwrapper import TreeTagger
import numpy as np
from scipy.spatial.distance import cosine
from juridico_site.settings import BASE_DIR
from collections import Counter
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from .models import *

vec = np.load(BASE_DIR+"/juridico/vecteurs_juridico.npz")
mots = list(vec["mots"])
#locale.setlocale(locale.LC_ALL, "fr_CA.utf-8")

mois_fr = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()


def str2date(datetime_iso: str) -> datetime:
    date_iso, _ = re.split(r'T', datetime_iso)
    y, m, d = tuple(int(i) for i in re.split(r'[/\-. ]+', date_iso))
    return date(y, m, d)

def date2str(d):
    return d.strftime("%d/%M/%Y")

def fortmatter_date(d):
    mois = mois_fr[d.month-1]
    return d.strftime("%-d {mois} %Y").format(mois=mois)

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


def add_direction(requete: Requete, texte: str, quand: str = ''):
    d, _ = Direction.objects.get_or_create(
        description = texte,
        quand = quand
    )
    d.save()
    r2r, _ = RessourceDeRequete.objects.get_or_create(
        requete=requete,
        resid=d.resid,
        poids=1.
    )
    r2r.save()

def add_organisation(requete, nom, desc, url):
    d, _ = Organisation.objects.get_or_create(
        description = desc,
        url = url,
        nom = nom
    )
    d.save()
    r2r, _ = RessourceDeRequete.objects.get_or_create(
        requete = requete,
        resid = d.resid,
        poids=1.
    )
    r2r.save()


def add_documentation(requete, *, nom='', desc='', url=''):
    d, _ = Documentation.objects.get_or_create(
        description = desc,
        url = url,
        nom = nom
    )
    d.save()
    r2r, _ = RessourceDeRequete.objects.get_or_create(
        requete = requete,
        resid = d.resid,
        poids=1.
    )
    r2r.save()


def add_camarade(requete: Requete, client: Client):
    organisation, _ = Organisation.objects.get_or_create(
        description = "",
        client=client
    )
    organisation.save()
    r2r, _ = RessourceDeRequete.objects.get_or_create(
        requete = requete,
        resid = organisation.resid,
        poids=1.
    )
    r2r.save()

def stocker_valeur(requete, nom, val):
    v, _ = Variable.objects.get_or_create(
        nom=nom,
        requete=requete,
        valeur=val
    )
    v.save()

def get_valeur(requete, nom):
    return Variable.objects.get(nom=nom).valeur

def question1(requete, reponse):
    if reponse.reponse.lower() == "oui":
        return 2
    else:
        return None #TODO: À changer

def question2(requete, reponse):
    r = reponse.reponse
    stocker_valeur(requete, "document_reçu", r)
    if r == "Avis d'augmentation de loyer et de modification d'une autre condition du bail":
        add_direction(
            requete,
            "Vous avez reçu un “Avis d'augmentation de loyer et de modification d'une autre condition du bail”."
            "Cet avis est nécessaire lorsque votre propriétaire veut modifier les conditions de votre bail,"
            "telle que le montant du loyer.",
            "[Info]"
        )
        add_documentation(
            requete,
            desc="Informations sur le renouvellement de bail et les augmentations de loyer",
            url="https://www.educaloi.qc.ca/capsules/le-renouvellement-de-bail-et-la-hausse-de-loyer"
        )
        return 3
    elif r == "Avis de reprise de logement":
        add_direction(
            requete,
            "Vous avez reçu un avis de reprise de logement. "
            "Votre propriétaire doit vous faire parvenir un tel avis écrit pour vous informer de son intention "
            "de reprendre le logement pour lui-même ou pour un membre de sa famille "
            "(soit ses enfants, ses parents ou une personne directement à sa charge)."
        )
        add_documentation(
            requete,
            desc="Informations sur la reprise de logement",
            url="https://www.educaloi.qc.ca/capsules/la-reprise-du-logement-et-leviction")
        return 4
    elif r == "Avis de réparation ou amélioration majeure":
        add_direction(
            requete,
            "Vous avez reçu un “Avis de réparation ou amélioration majeure”. "
            "Cet avis est nécessaire lorsque le propriétaire souhaite apporter des améliorations "
            "ou de faire des réparations majeures touchant votre logement.")
        add_documentation(
            requete,
            desc="Informations sur les réparations majeures en logement",
            url="https://www.rdl.gouv.qc.ca/fr/le-logement/travaux-majeurs"
        )
        # 4.C (n'existe pas encore)
    elif r == "Demande introductive d’instance":
        # Appartient au domaine familial
        return 9


def question3(requete: Requete, reponse: Reponse):
    # À quelle date avez-vous reçu ce document?
    stocker_valeur(requete, "date_reception", reponse.reponse)

    return 4
    # if reponse == "Avis d'augmentation de loyer et de modification d'une autre condition du bail":
    #     return 4
    # elif reponse in ("Avis de reprise de logement", "Avis de réparation ou amélioration majeure"):
    #     return 5

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
        add_direction(
            requete,
            "Selon les informations fournies, nous ne pouvons pas calculer si l’avis que votre propriétaire vous a "
            "envoyé respecte les délais. Pour déterminer cela, vous pouvez amener les papiers suivants : "
            "(1) votre bail écrit <strong>ET</strong> "
            "(2) l'avis de modification de bail , au comité logement le plus proche de chez vous, "
            "qui vous répondront gratuitement.")
        add_direction("""<strong>Lorsque l’avis respecte les délais</strong>,
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
        add_direction(requete, "Selon les informations fournies, nous ne pouvons pas calculer si l’avis que votre propriétaire vous a envoyé respecte les délais. Pour déterminer cela, vous pouvez amener les papiers suivants : (1) votre bail écrit <strong>ET</strong> (2) l'avis de modification de bail , au comité logement le plus proche de chez vous, qui vous répondront gratuitement.")
        add_direction(
            requete,
            """<strong>Lorsque l’avis respecte les délais</strong>,
                <ul>
                    <li>Vous disposez d’un mois pour répondre à cet avis. </li>
                    <li>Vous pouvez communiquer votre refus ou votre acceptation de la reprise des lieux. </li>
                    <li>Si vous ne répondez pas dans le délai de 1 mois, cela équivaut à un refus. </li>
                    <li>En cas de refus (ou si vous ne repondez pas), le propriétaire peut s’adresser à la Régie du logement.</li>
                    <li>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu. Et vous pouvez communiquer avec:</li>
                    <ul>
                        <li>Votre comité logement le plus proche pour vous aider dans une stratégie à présenter devant la Régie du logement.</li>
                        <li>Un avocat spécialiste en droit de logement.</li>
                    </ul>
                </ul>""")
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

        add_direction(
            requete=requete,
            texte="Selon l'information que vous nous avez fourni, l'avis de votre propriétaire respecte les délais (envoyé entre 3 et 6 mois avant la fin du bail)."
        )

        date_limite_reponse = date_reception + relativedelta(months=1)
        njours = (date_limite_reponse-date.today()).days

        add_direction(
            requete,
            """
        <p>Vous disposez d’un mois pour répondre à cet avis. Donc, vous avez jusqu’au %s (soit %d jours).</p>
        <p>Vous pouvez communiquer votre refus ou votre acceptation de la modification. Si vous ne répondez pas à l’avis, cela équivaudra à une acceptation des modifications.</p>
        <p>Si vous acceptez la modification, celle-ci prendra effet au terme de la durée du bail qui sera donc reconduit suivant les nouvelles modalités acceptées.</p>
        <p>Si vous refusez la modification, votre bail est tout de même reconduit et vous garder votre logement. À ce moment, vous pouvez:</p>
        <ul>
            <li>Essayer de vous entendre avec votre propriétaire pour une hausse que vous seriez capable d’accepter.</li>
            <li>Ne rien faire. Et dans ce cas, il est possible que votre propriétaire laisse tomber, comme il est possible qu’il s’adresse à la Régie du logement s’il souhaite quand même augmenter le loyer.</li>
            <li>Si vous refusez la modification, votre bail est tout de même reconduit et vous garder votre logement.</li>
            <li>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu.</li>
        </ul>
        """ % (fortmatter_date(date_limite_reponse), njours))

    elif duree_bail == "Bail de 12 mois et plus" and \
        (not rd_gt(d6mois,dmois_reception_fin_bail) or \
        rd_gt(d3mois, dmois_reception_fin_bail)):

        add_direction(
            requete,
            """<p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé n’est pas valide, car il ne respecte pas les délais.</p>
        <p>Ainsi, vous pouvez répondre qu’il n’est pas valide ou ne rien répondre.</p>""")

    elif duree_bail == "Bail de moins de 12 mois" and \
        rd_gt(d2mois,dmois_reception_fin_bail) and \
        not rd_gt(d1mois, dmois_reception_fin_bail):

        add_direction(
            requete,
            "Selon l'information que vous nous avez fourni, l'avis de votre propriétaire respecte les délais "
            "(envoyé entre 3 et 6 mois avant la fin du bail).")

        date_limite_reponse = date_reception + timedelta(months=1)
        njours = (date_limite_reponse-date.today()).days

        add_direction(
            requete,
            """
        <p>Vous disposez d’un mois pour répondre à cet avis. Donc, vous avez jusqu’au %s (soit %d jours).</p>
        <p>Vous pouvez communiquer votre refus ou votre acceptation de la modification. Si vous ne répondez pas à l’avis, cela équivaudra à une acceptation des modifications.</p>
        <p>Si vous acceptez la modification, celle-ci prendra effet au terme de la durée du bail qui sera donc reconduit suivant les nouvelles modalités acceptées.</p>
        <p>Si vous refusez la modification, votre bail est tout de même reconduit et vous garder votre logement. À ce moment, vous pouvez:</p>
        <ul>
            <li>Essayer de vous entendre avec votre propriétaire pour une hausse que vous seriez capable d’accepter.</li>
            <li>Ne rien faire. Et dans ce cas, il est possible que votre propriétaire laisse tomber, comme il est possible qu’il s’adresse à la Régie du logement s’il souhaite quand même augmenter le loyer.</li>
            <li>Si vous refusez la modification, votre bail est tout de même reconduit et vous garder votre logement.</li>
            <li>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu.</li>
        </ul>
        """ % (fortmatter_date(date_limite_reponse), njours))

    elif duree_bail == "Bail de moins de 12 mois" and \
        (not rd_gt(d2mois,dmois_reception_fin_bail) or \
        rd_gt(d1mois, dmois_reception_fin_bail)):

        add_direction(
            requete,
            """<p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé n’est pas valide, car il ne respecte pas les délais.</p>
        <p>Ainsi, vous pouvez répondre qu’il n’est pas valide ou ne rien répondre.</p>""")

    return -1

def question7(requete, reponse):
    stocker_valeur(requete, "date_de_modification_souhaitée", reponse.reponse)
    date_modifs = str2date(reponse.reponse)
    date_reception = str2date(get_valeur(requete, "date_reception"))

    dmois_reception_modifs = relativedelta(fin_bail, date_modifs)
    d1mois = relativedelta(months=1)
    d2mois = relativedelta(months=2)

    if rd_gt(d1mois,dmois_reception_fin_bail) and \
        not rd_gt(d2mois, dmois_reception_fin_bail): #équivaut à ≥ 3 mois & < 6 mois

        add_direction("Selon l'information que vous nous avez fourni, l'avis de votre propriétaire respecte les délais (envoyé entre 3 et 6 mois avant la fin du bail).")

        date_limite_reponse = date_reception + timedelta(months=1)
        njours = (date_limite_reponse-date.today()).days

        add_direction("""
        <p>Vous disposez d’un mois pour répondre à cet avis. Donc, vous avez jusqu’au %s (soit %d jours).</p>
        <p>Vous pouvez communiquer votre refus ou votre acceptation de la modification. Si vous ne répondez pas à l’avis, cela équivaudra à une acceptation des modifications.</p>
        <p>Si vous acceptez la modification, celle-ci prendra effet au terme de la durée du bail qui sera donc reconduit suivant les nouvelles modalités acceptées.</p>
        <p>Si vous refusez la modification, votre bail est tout de même reconduit et vous garder votre logement. À ce moment, vous pouvez:</p>
        <ul>
            <li>Essayer de vous entendre avec votre propriétaire pour une hausse que vous seriez capable d’accepter.</li>
            <li>Ne rien faire. Et dans ce cas, il est possible que votre propriétaire laisse tomber, comme il est possible qu’il s’adresse à la Régie du logement s’il souhaite quand même augmenter le loyer.</li>
            <li>Si vous refusez la modification, votre bail est tout de même reconduit et vous garder votre logement.</li>
            <li>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu.</li>
        </ul>
        """ % (fortmatter_date(date_limite_reponse), njours))

    else:

        add_direction("""<p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé n’est pas valide, car il ne respecte pas les délais.</p>
        <p>Ainsi, vous pouvez répondre qu’il n’est pas valide ou ne rien répondre.</p>""")

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

            add_direction("Selon l'information que vous nous avez fourni, l'avis de votre propriétaire respecte les délais (envoyé 6 mois ou plus avant la fin du bail).")

            date_limite_reponse = date_reception + timedelta(months=1)
            njours = (date_limite_reponse-date.today()).days

            add_direction("""
            <p>Vous disposez d’un mois pour répondre à cet avis. Donc, vous avez jusqu’au %s (soit %d jours).</p>
            <p>Vous pouvez communiquer votre refus ou votre acceptation de la reprise des lieux.</p>
            <p>SSi vous ne répondez pas dans le délai de 1 mois, cela équivaut à un refus.</p>
            <p>En cas de refus (ou si vous ne repondez pas), le propriétaire peut s’adresser à la Régie du logement.</p>
            <p>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu. Et vous pouvez communiquer avec&nbsp;:</p>
            <ul>
                <li>Votre comité logement le plus proche pour vous aider dans une stratégie à présenter devant la Régie du logement.</li>
                <li>Un avocat spécialiste en droit de logement.</li>
            </ul>
            """ % (fortmatter_date(date_limite_reponse), njours))

        else:
            add_direction("""<p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé n’est pas valide, car il ne respecte pas les délais.</p>
            <p>Ainsi, vous pouvez répondre qu’il n’est pas valide ou ne rien répondre.</p>""")
    elif duree_bail == "Bail de moins de 6 mois":
        if rd_gte(dmois_reception_fin_bail, d1mois):

            add_direction("Selon l'information que vous nous avez fourni, l'avis de votre propriétaire respecte les délais (envoyé 6 mois ou plus avant la fin du bail).")

            date_limite_reponse = date_reception + timedelta(months=1)
            njours = (date_limite_reponse-date.today()).days

            add_direction("""
            <p>Vous disposez d’un mois pour répondre à cet avis. Donc, vous avez jusqu’au %s (soit %d jours).</p>
            <p>Vous pouvez communiquer votre refus ou votre acceptation de la reprise des lieux.</p>
            <p>Si vous ne répondez pas dans le délai de 1 mois, cela équivaut à un refus.</p>
            <p>En cas de refus (ou si vous ne repondez pas), le propriétaire peut s’adresser à la Régie du logement.</p>
            <p>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu. Et vous pouvez communiquer avec&nbsp;:</p>
            <ul>
                <li>Votre comité logement le plus proche pour vous aider dans une stratégie à présenter devant la Régie du logement.</li>
                <li>Un avocat spécialiste en droit de logement.</li>
            </ul>
            """ % (fortmatter_date(date_limite_reponse), njours))

        else:
            add_direction("""<p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé n’est pas valide, car il ne respecte pas les délais.</p>
            <p>Ainsi, vous pouvez répondre qu’il n’est pas valide ou ne rien répondre.</p>""")
    return -1

def question19(requete,reponse):
    stocker_valeur(requete, "date_reprise_des_lieux", reponse.reponse)
    date_reprise_des_lieux = str2date(reponse.reponse)
    date_reception = str2date(get_valeur(requete, "date_reception"))

    dmois_reception_reprise = relativedelta(date_reprise_des_lieux, date_reception)
    d6mois = relativedelta(months=6)

    if rd_gte(dmois_reception_reprise, d6mois):

        add_direction("Selon l'information que vous nous avez fourni, l'avis de votre propriétaire respecte les délais (envoyé 6 mois ou plus avant la reprise des lieux prévue).")

        date_limite_reponse = date_reception + timedelta(months=1)
        njours = (date_limite_reponse-date.today()).days

        add_direction("""
        <p>Vous disposez d’un mois pour répondre à cet avis. Donc, vous avez jusqu’au %s (soit %d jours).</p>
        <p>Vous pouvez communiquer votre refus ou votre acceptation de la reprise des lieux.</p>
        <p>Si vous ne répondez pas dans le délai de 1 mois, cela équivaut à un refus.</p>
        <p>En cas de refus (ou si vous ne repondez pas), le propriétaire peut s’adresser à la Régie du logement.</p>
        <p>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu. Et vous pouvez communiquer avec&nbsp;:</p>
        <ul>
            <li>Votre comité logement le plus proche pour vous aider dans une stratégie à présenter devant la Régie du logement.</li>
            <li>Un avocat spécialiste en droit de logement.</li>
        </ul>
        """ % (fortmatter_date(date_limite_reponse), njours))

    else:
        add_direction("""<p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé n’est pas valide, car il ne respecte pas les délais.</p>
        <p>Ainsi, vous pouvez répondre qu’il n’est pas valide ou ne rien répondre.</p>""")

    return -1

def question20(requete,reponse):
    # Date de début des travaux
    stocker_valeur(requete,"date_debut_travaux", reponse.reponse)

    date_reception = str2date(get_valeur(requete, "date_reception"))
    date_debut_travaux = str2date(reponse.reponse)

    return 21

def question21(requete,reponse):
    date_reception = str2date(get_valeur(requete, "date_reception"))
    date_debut_travaux = str2date(get_valeur(requete, "date_debut_travaux"))
    njours = (date_debut_travaux-date_reception).days
    d_reception_debut_travaux = relativedelta(date_debut_travaux,date_reception)
    rep = reponse.reponse.strip().lower()
    d3mois = relativedelta(months=3)

    if rep == "non":
        if njours < 10:
            add_direction("""
            <p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé ne respecte pas les délais, car il est nécessaire d’envoyer l’avis de réparation au moins 10 jours avant le début de travaux.</p>
            <p>Cet avis devait, de plus, mentionner les choses suivantes&nbsp;:</p>
            <ul>
            <li>la nature des travaux</li>
            <li>la date du début des travaux et l'estimation de leur durée</li>
            <li>toutes les autres conditions dans lesquelles s'effectueront les travaux s'ils sont susceptibles de diminuer sérieusement la jouissance des lieux</li>
            <li>Et s’il y avait une évacuation, l’avis devait en plus mentionner la période d’évacuation et le montant offert à titre d’indemnité pour couvrir les dépenses liées à celle-ci</li>
            </ul>
            <p>Vous pouvez communiquer avec lui pour lui énoncer que son avis ne respecte pas les délais.</p>
            <p>Dans ce cas, votre propriétaire pourra peut-être vous renvoyer un avis qui respecte les délais.</p>
            """)
        else:
            add_direction("""
            <p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé respecte les délais.</p>
            <p>Cet avis devait mentionner les choses suivantes&nbsp;:</p>
            <ul>
            <li>la nature des travaux</li>
            <li>la date du début des travaux et l'estimation de leur durée</li>
            <li>toutes les autres conditions dans lesquelles s'effectueront les travaux s'ils sont susceptibles de diminuer sérieusement la jouissance des lieux</li>
            <li>Et s’il y avait une évacuation, l’avis devait en plus mentionner la période d’évacuation et le montant offert à titre d’indemnité pour couvrir les dépenses liées à celle-ci</li>
            </ul>
            """)
            date_max = date_reception + timedelta(days=10)
            add_direction("""
            <p>Vous disposez d’un délai de 10 jours pour répondre à cet avis. Donc, vous avez jusqu’au {date_max}.</p>
            <p>Vous pouvez refuser ou accepter l’évacuation.</p>
            <p>Si vous ne répondez pas, vous êtes présumé avoir refusé de quitter les lieux.</p>
            <p>Si vous refusez (ou si vous ne répondez pas), votre propriétaire pourra alors, dans les 10 jours suivant votre refus, s'adresser à la Régie du logement qui statuera sur l'opportunité de l'évacuation et pourra fixer les conditions qu'elle estime justes et raisonnables.</p>
            <p>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu. Et vous pouvez communiquer avec&nbsp;:</p>
            <ul>
            <li>Votre comité logement le plus proche pour vous aider dans une stratégie à présenter devant la Régie du logement</li>
            <li>Un avocat spécialiste en droit de logement</li>
            </ul>
            """.format())
    if rep == "oui":
        if rd_gt(d3mois, d_reception_debut_travaux):
            add_direction("""
            <p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé ne respecte pas les délais, car il est nécessaire d’envoyer l’avis de réparation au moins 3 mois avant le début de travaux, lorsque l’évacuation sera d’une semaine ou plus.</p>
            <p>Cet avis devait, de plus, mentionner les choses suivantes&nbsp;:</p>
            <ul>
            <li>la nature des travaux</li>
            <li>la date du début des travaux et l'estimation de leur durée</li>
            <li>toutes les autres conditions dans lesquelles s'effectueront les travaux s'ils sont susceptibles de diminuer sérieusement la jouissance des lieux</li>
            <li>La période d’évacuation</li>
            <li>Le montant offert à titre d’indemnité pour couvrir les dépenses liées à l’évacuation des lieux</li>
            </ul>
            <p>Vous pouvez communiquer avec votre propriétaire pour lui énoncer que son avis ne respecte pas les délais.</p>
            <p>Dans ce cas, votre propriétaire pourra peut-être vous renvoyer un avis qui respecte les délais.</p>
            """)
        else:
            add_direction("""
            <p>Selon les informations fournies, l’avis que votre propriétaire vous a envoyé respecte les délais.</p>
            <p>Cet avis devait mentionner les choses suivantes&nbsp;:</p>
            <ul>
            <li>la nature des travaux</li>
            <li>la date du début des travaux et l'estimation de leur durée</li>
            <li>toutes les autres conditions dans lesquelles s'effectueront les travaux s'ils sont susceptibles de diminuer sérieusement la jouissance des lieux</li>
            <li>La période d’évacuation</li>
            <li>Le montant offert à titre d’indemnité pour couvrir les dépenses liées à l’évacuation des lieux</li>
            </ul>
            """)
            date_max = date_reception + timedelta(days=10)
            add_direction("""
            <p>Vous disposez d’un délai de 10 jours pour répondre à cet avis. Donc, vous avez jusqu’au {date_max}.</p>
            <p>Vous pouvez refuser ou accepter l’évacuation.</p>
            <p>Si vous ne répondez pas, vous êtes présumé avoir refusé de quitter les lieux.</p>
            <p>Si vous refusez (ou si vous ne répondez pas), votre propriétaire pourra alors, dans les 10 jours suivant votre refus, s'adresser à la Régie du logement qui statuera sur l'opportunité de l'évacuation et pourra fixer les conditions qu'elle estime justes et raisonnables.</p>
            <p>Si le propriétaire s’adresse à la Régie du logement, celle-ci vous transmettra un avis d’audience en temps et lieu. Et vous pouvez communiquer avec&nbsp;:</p>
            <ul>
            <li>Votre comité logement le plus proche pour vous aider dans une stratégie à présenter devant la Régie du logement</li>
            <li>Un avocat spécialiste en droit de logement</li>
            </ul>
            """.format())
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
    F8 = get_valeur(requete, "autorepresentation")
    F5 = str2date(get_valeur(requete,"date_reception"))
    F7 = str2date(get_valeur(requete,"date_avis_presentation"))
    F9 = reponse.reponse.strip().lower()

    if F8 == "oui":
        if F1 == "non":
            add_direction("Vous devez vous présenter à la cour le {date_cour} et indiquer votre intention de contester les conclusions dans la demande.".format(date_cour=F7))
        else:
            add_direction("""
            <p>Si vous désirez vous représentez seul, vous devez remplir le formulaire <a href="https://www.justice.gouv.qc.ca/fileadmin/user_upload/contenu/documents/Fr__francais_/centredoc/formulaires/vos-differends/sj554.pdf" target="_blank">"Réponse" (SJ-554)</a> et le déposer au greffe du tribunal indiqué en haut de la demande.</p>
            <p>Notez que vous aurez à défrayer des frais.</p>
            """)
    if F2 == "oui":
        add_direction("""<p>Vous êtes admissible au programme provincial de médiation familiale. Vous avez donc droit à 5 heures gratuite de médiation.</p>
        <p>Contactez la partie adverse pour proposer la médiation. Vous trouverez ci-bas une liste de médiateurs accrédités près de vous.</p>""")
