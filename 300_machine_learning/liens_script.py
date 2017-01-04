# Avant d'exécuter ce script :
# `alter table article_2 add numero_ligne serial;`

import sys
import pickle
import os

import psycopg2

import jetons
import liens


assert len(sys.argv) == 3
nb_proc = int(sys.argv[1])
id_proc = int(sys.argv[2])

dossier_data = '/home/michel/loi/data/'


connection = psycopg2.connect(dbname='loi', user='loi', password='baba')
curseur = connection.cursor()

curseur.execute("select id_, bloc_textuel from article_2 where mod(numero_ligne, %s) = %s;", (nb_proc, id_proc,))
resultats = curseur.fetchall()

curseur.close()
connection.close()


liste_representations = ''
for id_, contenu_brut in resultats:
    position_mots, contenu_mots = jetons.transformation_jetons(contenu_brut)
    liste_liens = liens.trouve_liens(contenu_brut, position_mots, contenu_mots)
    
    liste_representations += liens.representation_liens(contenu_brut, liste_liens)

nom_fichier = os.path.join(dossier_data, 'representation_lien', '{:05}_sur_{}.txt'.format(id_proc, nb_proc))
with open(nom_fichier, 'w') as f:
    f.write(liste_representations)
