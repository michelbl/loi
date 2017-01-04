import jetons


jetons_importants = {
    '__date',
    '__num_longue',
    '__arabe',
    '__romain_min',
    '__romain_maj',
    '__arabe_comp',
    '__num_courte',
    '__latin',
    '__lettre_min',
    '__lettre_maj',
    '__ordinal_o',
    '__cardinal_fr',
    '__ordinal_fr',
}

mots_importants = {
    
    'loi',
    'lois',
    'organique',
    'organiques',
    'décret',
    'décrets',
    'code',
    'codes',
    'avenant',
    'avenants',
    'circulaire',
    'circulaires',
    'arrêté',
    'arrêtés',
    'règlement',
    'règlements',

    'partie',
    'parties',
    'livre',
    'livres',
    'titre',
    'titres',
    'chapitre',
    'chapitres',
    'section',
    'sections',
    'article',
    'articles',
    'alinea',
    'alineas',
    'alinéa',
    'alinéas',
    'annexe',
    'annexes',

    'susvisé',
    'susvisés',
    'susvisée',
    'susvisées',
    'précité',
    'précités',
    'précitée',
    'précitées',
    'modifié',
    'modifiés',
    'modifiée',
    'modifiées',
    'relatif',
    'relatifs',
    'relative',
    'relatives',
    'modificatif',
    'modificatifs',
    'modificative',
    'modificatives',

    'présent',
    'présents',
    'présente',
    'présentes',
    'précédent',
    'précédents',
    'précédente',
    'précédentes',
    'suivant',
    'suivants',
    'suivante',
    'suivantes',
    
    'no',
    'n°',
}

ensemble_mots_importants = set(mots_importants)


def trouve_liens_paragraphe(contenu_brut, position_mots_dans_paragraphe, contenu_mots_dans_paragraphe):
    liens = []
    i = 0
    while i < len(position_mots_dans_paragraphe):
        debut, fin = position_mots_dans_paragraphe[i]
        mot = contenu_brut[debut:fin].lower()
        contenu = contenu_mots_dans_paragraphe[i]
        if (contenu in jetons_importants) or ((contenu == None) and (mot in mots_importants)):
            lien_positions = [(debut, fin)]
            lien_contenus = [contenu]
            i += 1
            while True:
                mots_suivants = []
                contenus_suivants = []
                for j in range(min(3, len(position_mots_dans_paragraphe) - i)):
                    debut, fin = position_mots_dans_paragraphe[i+j]
                    mot = contenu_brut[debut:fin].lower()
                    contenu = contenu_mots_dans_paragraphe[i+j]
                    if contenu:
                        contenus_suivants.append(contenu)
                    else:
                        mots_suivants.append(mot)

                if not (
                        (set(mots_suivants) & mots_importants) or
                        (set(contenus_suivants) & jetons_importants)
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
            contenu if contenu else contenu_brut[mot[0]:mot[1]]
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



