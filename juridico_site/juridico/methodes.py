from treetaggerwrapper import TreeTagger
import numpy as np
from scipy.spatial.distance import cosine
from juridico_site.settings import BASE_DIR

vec = np.load(BASE_DIR+"/juridico/vecteurs_juridico.npz")
mots = list(vec["mots"])

def desc2domaine(description_cas, dom_logement=1, dom_famille=2):
    tagger = TreeTagger(TAGLANG="fr")
    v = np.zeros(len(mots))
    t = [ ln.split("\t") for ln in tagger.tag_text(description_cas) ]
    t = [ i[2] for i in t if len(i)==3 ]
    t = [ i for i in t in i in mots ]

    nmots = float(len(t))

    for k, val in Counter(t).items():
        v[mots.index(k)] = val / nmots

    dfamille = cosine(v, vec["famille"])
    dlogement = cosine(v, vec["logement"])

    if dlogement < dfamille:
        return dom_logement
    else:
        return dom_famille
