import psycopg2

import jetons


def charge_version(id_):
    connection = psycopg2.connect(dbname='loi', user='loi', password='baba')
    curseur = connection.cursor()

    curseur.execute("select notice, visas, signataires, tp, nota, abro, rect, sm from article_2 where id_ = %s;", (id_,))
    liste_contenu = curseur.fetchall()

    curseur.close()
    connection.close()

    assert(len(liste_contenu) == 1)

    notice, visas, signataires, tp, nota, abro, rect, sm = liste_contenu[0]
    
    return notice, visas, signataires, tp, nota, abro, rect, sm

def charge_article(id_):
    connection = psycopg2.connect(dbname='loi', user='loi', password='baba')
    curseur = connection.cursor()

    curseur.execute("select nota, sm, bloc_textuel from article_2 where id_ = %s;", (id_,))
    liste_contenu = curseur.fetchall()

    curseur.close()
    connection.close()

    assert(len(liste_contenu) == 1)

    nota, sm, bloc_textuel = liste_contenu[0]
    
    return nota, sm, bloc_textuel

def trouve_arabe_comp(contenu_brut, position_mots, contenu_mots):
    liste_arabe_comp_position = []
    for position_mots_dans_paragraphe, contenu_mots_dans_paragraphe in zip(position_mots, contenu_mots):
        liste_arabe_comp_position += [
            m
            for m, c in zip(position_mots_dans_paragraphe, contenu_mots_dans_paragraphe)
            if c == '__arabe_comp'
        ]
        
    liste_arabe_comp = [contenu_brut[d:f] for d, f in liste_arabe_comp_position]
    
    
    connection = psycopg2.connect(dbname='loi', user='loi', password='baba')
    curseur = connection.cursor()

    liste_texte = []
    for arabe_comp in liste_arabe_comp:
        curseur.execute("select cid, id_, titrefull from texte_version where num = %s;", (arabe_comp,))
        resultats = curseur.fetchall()
        
        liste_cid = [r[0] for r in resultats]
        if len(set(liste_cid)) == 1:
            liste_texte.append(liste_cid[0])

    curseur.close()
    connection.close()
        
    return liste_texte

def trouve_liens_article(id_):
    nota, sm, bloc_textuel = charge_article(id_)

    contenu_brut = nota + sm + bloc_textuel

    position_mots, contenu_mots = jetons.transformation_jetons(contenu_brut)

    liste_texte = trouve_arabe_comp(contenu_brut, position_mots, contenu_mots)
    
    return liste_texte

def trouve_liens_version(id_):
    notice, visas, signataires, tp, nota, abro, rect, sm = charge_version(id_)

    contenu_brut = notice, visas, signataires, tp, nota, abro, rect, sm

    position_mots, contenu_mots = jetons.transformation_jetons(contenu_brut)

    liste_texte = trouve_arabe_comp(contenu_brut, position_mots, contenu_mots)
    
    return liste_texte
