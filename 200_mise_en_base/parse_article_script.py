import sys
import pickle
import os

import parse_article

assert len(sys.argv) == 3
nb_proc = int(sys.argv[1])
id_proc = int(sys.argv[2])

dossier_data = '/home/michel/loi/data/'
with open(dossier_data + 'liste_article.pickle', 'rb') as f:
    liste_article = pickle.load(f)

for base_origine, categorie, cid, id_ in liste_article[id_proc::nb_proc]:
    nom_fichier = dossier_data + 'parse_article/' + cid

    if os.path.isfile(nom_fichier):
        continue

    try:
        valeurs = parse_article.parse_un_article(base_origine, categorie, cid, id_)
    except:
        raise ValueError(cid)

    with open(nom_fichier, 'wb') as f:
        pickle.dump(valeurs, f)
