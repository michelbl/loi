import sys
import pickle
import os

import psycopg2

import parse_texte

assert len(sys.argv) == 3
nb_proc = int(sys.argv[1])
id_proc = int(sys.argv[2])

dossier_data = '/home/michel/loi/data/'
with open(dossier_data + 'liste_texte.pickle', 'rb') as f:
    liste_texte = pickle.load(f)

connection = psycopg2.connect(dbname='loi', user='loi', password='baba')
curseur = connection.cursor()

for base_origine, categorie, cid in liste_texte[id_proc::nb_proc]:
    nom_fichier = dossier_data + 'parse_texte/' + cid

    if os.path.isfile(nom_fichier):
        continue

    try:
        liste_id_, valeurs_struct_par_id_, valeurs_version_par_id_ = parse_texte.parse_cid(cid, curseur)
    except:
        raise ValueError(cid)

    with open(nom_fichier, 'wb') as f:
        pickle.dump((liste_id_, valeurs_struct_par_id_, valeurs_version_par_id_), f)

curseur.close()
connection.close()
