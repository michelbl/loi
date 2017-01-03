import xml.etree.ElementTree as ElementTree
import re

import psycopg2


# Trouve le contenu d'un article

def charge_contenu_article(id_):
    connection = psycopg2.connect(dbname='loi', user='loi', password='baba')
    curseur = connection.cursor()

    curseur.execute("select bloc_textuel from article_2 where id_ = %s;", (id_,))
    liste_contenu = curseur.fetchall()

    curseur.close()
    connection.close()

    assert(len(liste_contenu) == 1)

    bloc_textuel = liste_contenu[0][0]
    
    return bloc_textuel


# Enlève les balises HTML

def separation(contenu_brut, patron):
    liste_debut = []
    liste_fin = [0]
    for balise_match in re.finditer(patron, contenu_brut):
        debut, fin = balise_match.span()
        liste_debut.append(debut)
        liste_fin.append(fin)
    liste_debut.append(len(contenu_brut))

    position_paragraphes = []
    liste_paragraphe = []
    for debut, fin in zip(liste_fin, liste_debut):
        position_paragraphes.append((debut, fin))
        liste_paragraphe.append(contenu_brut[debut:fin])
        
    return position_paragraphes, liste_paragraphe

def suppression_HTML(contenu_brut):
    return separation(contenu_brut, '<[^<]+?>')


# Séparation en paragraphes

def separation_paragraphe(contenu_brut, position_paragraphes):
    position_paragraphes_nouveau = []
    
    for debut, fin in position_paragraphes:
        paragraphe = contenu_brut[debut:fin]
        position_sous_paragraphes, _ = separation(paragraphe, '\n')
        position_sous_paragraphes = [(d + debut, f + debut) for d, f in position_sous_paragraphes if d!=f]
        position_paragraphes_nouveau += position_sous_paragraphes
        
    return position_paragraphes_nouveau


# Séparation en mots

def separation_paragraphe_en_mots(contenu_brut, position_paragraphes):
    position_mots = []
    
    for debut, fin in position_paragraphes:
        paragraphe = contenu_brut[debut:fin]
        position_mots_dans_paragraphe, _ = separation(paragraphe, '[ \t\r\n\xa0]+')
        position_mots_dans_paragraphe = [(d + debut, f + debut) for d, f in position_mots_dans_paragraphe if d!=f]
        if len(position_mots_dans_paragraphe) > 0:
            position_mots.append(position_mots_dans_paragraphe)
        
    return position_mots


# Séparation par les apostrophes, en gardant les apostrophes

liste_apostrophe = ["'", '’']

# invariant : separe_apostrophe_mot n'est jamais appelé sur un mot vide
def separe_apostrophe_mot(contenu_brut, debut, fin, apostrophe):
    nouveaux_mots = []
    index = contenu_brut.find(apostrophe, debut, fin)
    if index == -1:
        nouveaux_mots.append((debut, fin))
    else:
        if debut < index:
            nouveaux_mots.append((debut, index))
        nouveaux_mots.append((index, index + 1))
        if index + 1 < fin:
            nouveaux_mots += separe_apostrophe_mot(contenu_brut, index + 1, fin, apostrophe)
    return nouveaux_mots

def separe_apostrophe_paragraphe(contenu_brut, position_mots_dans_paragraphe, apostrophe):
    nouveaux_mots = []
    for debut, fin in position_mots_dans_paragraphe:
        nouveaux_mots += separe_apostrophe_mot(contenu_brut, debut, fin, apostrophe)
        
    return nouveaux_mots

def separe_apostrophe(contenu_brut, position_mots, apostrophe):
    nouveau_position_mots = []
    for position_mots_dans_paragraphe in position_mots:
        nouveau_position_mots.append(
            separe_apostrophe_paragraphe(contenu_brut, position_mots_dans_paragraphe, apostrophe))
        
    return nouveau_position_mots


# Séparation de la ponctuation

liste_ponctuation = ['.', ',', ';', ':', '!', '?', "'", '"', '(', ')', '[', ']', '«', '»']

def separe_ponctuation_mot(contenu_brut, debut, fin):
    nouveaux_mots = []
    while (debut < fin) and (contenu_brut[debut] in liste_ponctuation):
        nouveaux_mots.append((debut, debut + 1))
        debut += 1
        
    nouveaux_mots_inverse = []
    while (debut < fin) and (contenu_brut[fin - 1] in liste_ponctuation):
        nouveaux_mots_inverse.append((fin - 1, fin))
        fin -= 1
        
    if debut < fin:
        nouveaux_mots.append((debut, fin))

    nouveaux_mots += nouveaux_mots_inverse[::-1]

    return nouveaux_mots

def separe_ponctuation_paragraphe(contenu_brut, position_mots_dans_paragraphe):
    nouveaux_mots = []
    for debut, fin in position_mots_dans_paragraphe:
        nouveaux_mots += separe_ponctuation_mot(contenu_brut, debut, fin)
        
    return nouveaux_mots

def separe_ponctuation(contenu_brut, position_mots):
    nouveau_position_mots = []
    for position_mots_dans_paragraphe in position_mots:
        nouveau_position_mots.append(
            separe_ponctuation_paragraphe(contenu_brut, position_mots_dans_paragraphe))
        
    return nouveau_position_mots


# Transforme les numéros en jetons
# Ceci permet de réduire la taille du vocabulaire en regroupant les nombres de même type.

# Fonction auxilliaires

def est_entier(v):
    for c in v:
        if c not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            return False
    if not v:
        return False
    if v[0] == '0':
        return False
    return True

def passe_paragraphe(
        contenu_brut,
        position_mots_dans_paragraphe, contenu_mots_dans_paragraphe,
        nb_mots, est_numero, jeton
        ):
    nouvelles_positions = []
    nouveaux_contenus = []
    
    i = 0
    while i < len(position_mots_dans_paragraphe):
        if (i + nb_mots <= len(position_mots_dans_paragraphe)) and (est_numero(contenu_brut, position_mots_dans_paragraphe[i:i+nb_mots])):
            nouvelles_positions.append((position_mots_dans_paragraphe[i][0], position_mots_dans_paragraphe[i+nb_mots-1][1]))
            nouveaux_contenus.append(jeton)
            i += nb_mots
        else:
            nouvelles_positions.append(position_mots_dans_paragraphe[i])
            nouveaux_contenus.append(contenu_mots_dans_paragraphe[i])
            i += 1

    return nouvelles_positions, nouveaux_contenus

def passe(contenu_brut, position_mots, contenu_mots, nb_mots, est_numero, jeton):
    nouvelles_positions = []
    nouveaux_contenus = []
    for position_mots_dans_paragraphe, contenu_mots_dans_paragraphe in zip(position_mots, contenu_mots):
        nouvelles_positions_dans_paragraphe, nouveaux_contenus_dans_paragraphe = passe_paragraphe(
            contenu_brut,
            position_mots_dans_paragraphe, contenu_mots_dans_paragraphe,
            nb_mots, est_numero, jeton)
        
        nouvelles_positions.append(nouvelles_positions_dans_paragraphe)
        nouveaux_contenus.append(nouveaux_contenus_dans_paragraphe)
        
    return nouvelles_positions, nouveaux_contenus

# passe_paragraphe avec nb_mots = 1
def passe_paragraphe_bijective(
        contenu_brut,
        position_mots_dans_paragraphe, contenu_mots_dans_paragraphe,
        liste_est_numero, jetons
        ):
    nouveaux_contenus = []
    
    for i in range(len(position_mots_dans_paragraphe)):
        debut, fin = position_mots_dans_paragraphe[i]
        contenu = contenu_mots_dans_paragraphe[i]
        for est_numero, jeton in zip(liste_est_numero, jetons):
            if est_numero(contenu_brut, debut, fin):
                contenu = jeton
                continue
        nouveaux_contenus.append(contenu)

    return nouveaux_contenus

# passe avec nb_mots = 1 mais avec plusieurs tests
def passe_bijective(contenu_brut, position_mots, contenu_mots, liste_est_numero, jetons):
    nouveaux_contenus = []
    for position_mots_dans_paragraphe, contenu_mots_dans_paragraphe in zip(position_mots, contenu_mots):
        nouveaux_contenus_dans_paragraphe = passe_paragraphe_bijective(
            contenu_brut,
            position_mots_dans_paragraphe, contenu_mots_dans_paragraphe,
            liste_est_numero, jetons)
        
        nouveaux_contenus.append(nouveaux_contenus_dans_paragraphe)
        
    return nouveaux_contenus

def est_regex(contenu_brut, debut, fin, regex):
    mot = contenu_brut[debut:fin]
    return bool(re.match(regex, mot))

def joli_affichage(contenu_brut, position_mots, contenu_mots):
    for position_mots_dans_paragraphe, contenu_mots_dans_paragraphe in zip(position_mots, contenu_mots):
        print(' | '.join(
            [
                contenu_brut[mot[0]:mot[1]] + (' (' + contenu + ')' if contenu else '')
                for mot, contenu in zip(position_mots_dans_paragraphe, contenu_mots_dans_paragraphe)
            ]))

        
# Différents types de numérotations

liste_est_numero = []
jetons = []

# Dates

jeton_date = '__date'

def est_date(contenu_brut, mots):
    d, f = mots[0]
    mot_jour = contenu_brut[d:f]
    if est_entier(mot_jour) or mot_jour == '1er':
        if mot_jour == '1er':
            num_jour = 1
        else:
            num_jour = int(mot_jour)
        if num_jour >= 1 and num_jour <= 31:
            d, f = mots[1]
            mot_mois = contenu_brut[d:f]
            if mot_mois in ['janvier', 'février', 'mars', 'avril',
                            'mai', 'juin', 'juillet', 'août',
                            'septembre', 'octobre', 'novembre', 'décembre']:
                d, f = mots[2]
                mot_annee = contenu_brut[d:f]
                if est_entier(mot_annee):
                    num_annee = int(mot_annee)
                    if num_annee >= 1000 and num_annee <= 2500:
                        return True
    return False

# Nombres arabes

jeton_arabe = '__arabe'

def est_arabe(contenu_brut, debut, fin):
    mot = contenu_brut[debut:fin]
    return est_entier(mot)

liste_est_numero.append(est_arabe)
jetons.append(jeton_arabe)

# Nombres romains

regex_romain_minuscule = r'^(x{0,3})(ix|iv|v?i{0,4})$'
regex_romain_majuscule = r'^(X{0,3})(IX|IV|V?I{0,4})$'

jeton_romain_minuscule = '__romain_min'
jeton_romain_majuscule = '__romain_maj'

def est_romain_min(contenu_brut, debut, fin):
    return est_regex(contenu_brut, debut, fin, regex_romain_minuscule)

def est_romain_maj(contenu_brut, debut, fin):
    return est_regex(contenu_brut, debut, fin, regex_romain_majuscule)

liste_est_numero.append(est_romain_min)
jetons.append(jeton_romain_minuscule)

liste_est_numero.append(est_romain_maj)
jetons.append(jeton_romain_majuscule)

# Nombres arabes composés (ex: loi 2008-243, article L. 1223-6)

regex_arabe_comp = r'^\d+-\d+$'

jeton_arabe_comp = '__arabe_comp'

def est_arabe_comp(contenu_brut, debut, fin):
    return est_regex(contenu_brut, debut, fin, regex_arabe_comp)

liste_est_numero.append(est_arabe_comp)
jetons.append(jeton_arabe_comp)

# Numérotation code (ex: L. 1223-6, R. 1223-7, L1223-6, R1223-6)
# Pour l'instant, la manière longue (X. DDD-DDD) n'est pas traitée (déjà __arabe_comp pour réduire la cardinalité)

regex_num_article = r'^(L|R)\d+-\d+$'

jeton_num_article = '__num_article'

def est_num_article(contenu_brut, debut, fin):
    return est_regex(contenu_brut, debut, fin, regex_num_article)

liste_est_numero.append(est_num_article)
jetons.append(jeton_num_article)

# Adverbes multiplicatifs latins (bit, ter...)

latins = [
    'bis',
    'ter',
    'quater',
    'quinquies',
    'sexies',
    'septies',
    'octies',
    'nonies',
    'decies',
    'undecies',
    'duodecies',
    'terdecies',
    'quaterdecies',
    'quindecies',
    'sedecies',
    'sexdecies',
    'septdecies',
    'duodevicies',
    'octodecies',
    'undevicies',
    'novodecies',
    'vicies',
]

jeton_latin = '__latin'

def est_latin(contenu_brut, debut, fin):
    mot = contenu_brut[debut:fin]
    return mot in latins

liste_est_numero.append(est_latin)
jetons.append(jeton_latin)

# Ordinaux ° (ex: 2°)

regex_ordinal_o = r'^\d+°$'
jeton_ordinal_o = '__ordinal_o'

def est_ordinal_o(contenu_brut, debut, fin):
    return est_regex(contenu_brut, debut, fin, regex_ordinal_o)

liste_est_numero.append(est_ordinal_o)
jetons.append(jeton_ordinal_o)


# Pipeline

def transformation_jetons(contenu_brut):
    position_paragraphes, _ = suppression_HTML(contenu_brut)
    
    position_paragraphes = separation_paragraphe(contenu_brut, position_paragraphes)
    
    position_mots = separation_paragraphe_en_mots(contenu_brut, position_paragraphes)
    
    for apostrophe in liste_apostrophe:
        position_mots = separe_apostrophe(contenu_brut, position_mots, apostrophe)
    
    position_mots = separe_ponctuation(contenu_brut, position_mots)
    
    contenu_mots = [[None] * len(l) for l in position_mots]
    
    nouvelles_positions, nouveaux_contenus = passe(contenu_brut, position_mots, contenu_mots, 3, est_date, jeton_date)
    
    nouveaux_contenus = passe_bijective(contenu_brut, nouvelles_positions, nouveaux_contenus, liste_est_numero, jetons)
    
    return nouvelles_positions, nouveaux_contenus
