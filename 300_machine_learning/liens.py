from unidecode import unidecode

import jetons


def trouve_liens_paragraphe(contenu_brut, position_mots_dans_paragraphe, contenu_mots_dans_paragraphe):
    liens = []
    i = 0
    while i < len(position_mots_dans_paragraphe):
        debut, fin = position_mots_dans_paragraphe[i]
        mot = unidecode(contenu_brut[debut:fin]).lower()
        contenu = contenu_mots_dans_paragraphe[i]
        if (contenu in jetons.jetons_importants) or ((contenu == None) and (mot in jetons.mots_importants)):
            lien_positions = [(debut, fin)]
            lien_contenus = [contenu]
            i += 1
            while True:
                mots_suivants = []
                contenus_suivants = []
                for j in range(min(3, len(position_mots_dans_paragraphe) - i)):
                    debut, fin = position_mots_dans_paragraphe[i+j]
                    mot = unidecode(contenu_brut[debut:fin]).lower()
                    contenu = contenu_mots_dans_paragraphe[i+j]
                    if contenu:
                        contenus_suivants.append(contenu)
                    else:
                        mots_suivants.append(mot)

                if not (
                        (set(mots_suivants) & jetons.mots_importants) or
                        (set(contenus_suivants) & jetons.jetons_importants)
                ):
                    break
                
                debut, fin = position_mots_dans_paragraphe[i]
                mot = contenu_brut[debut:fin]
                contenu = contenu_mots_dans_paragraphe[i]
                
                lien_positions.append((debut, fin))
                lien_contenus.append(contenu)
                i += 1
                
            if len(lien_positions) > 1:
                liens.append((lien_positions, lien_contenus))
 
        i += 1
    
    return liens


def trouve_liens(contenu_brut, position_mots, contenu_mots):
    liens = []
    for position_mots_dans_paragraphe, contenu_mots_dans_paragraphe in zip(position_mots, contenu_mots):
        liens_dans_paragraphe = trouve_liens_paragraphe(
            contenu_brut, position_mots_dans_paragraphe, contenu_mots_dans_paragraphe)
        
        liens.append(liens_dans_paragraphe)
        
    return liens


def joli_affichage_liens(contenu_brut, liens):
    for liens_dans_paragraphe in liens:
        for lien_positions, lien_contenus in liens_dans_paragraphe:
            print(' | '.join(
                [
                    contenu_brut[mot[0]:mot[1]] + (' (' + contenu + ')' if contenu else '')
                    for mot, contenu in zip(lien_positions, lien_contenus)
                ]))
        
        
def representation_lien(contenu_brut, lien_positions, lien_contenus):
    return ' '.join(
        [
            contenu if contenu else unidecode(contenu_brut[mot[0]:mot[1]]).lower()
            for mot, contenu in zip(lien_positions, lien_contenus)
        ]) + '\n'


def representation_liens_dans_paragraphe(contenu_brut, liens_dans_paragraphe):
    return ''.join([
        representation_lien(contenu_brut, lien_positions, lien_contenus)
        for lien_positions, lien_contenus in liens_dans_paragraphe
    ])


def representation_liens(contenu_brut, liens):
    return ''.join([
        representation_liens_dans_paragraphe(contenu_brut, liens_dans_paragraphe)
        for liens_dans_paragraphe in liens
    ])



