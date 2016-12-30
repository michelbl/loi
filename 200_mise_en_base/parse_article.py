import os
import sys
import xml.etree.ElementTree as ElementTree
import collections
from collections import Counter

import psycopg2


racine_legi = '/home/michel/legi_plat/'
racine_jorf = '/home/michel/jorf_plat/'


class FrozenDict(collections.Mapping):
    """Mike Graham http://stackoverflow.com/questions/2703599/what-would-a-frozen-dict-be"""

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        # It would have been simpler and maybe more obvious to 
        # use hash(tuple(sorted(self._d.iteritems()))) from this discussion
        # so far, but this solution is O(n). I don't know what kind of 
        # n we are going to run into, but sometimes it's hard to resist the 
        # urge to optimize when it will gain improved algorithmic performance.
        if self._hash is None:
            self._hash = 0
            for pair in self.items():
                self._hash ^= hash(pair)
        return self._hash
    
    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self._d))
    
    def __str__(self):
        return self.__repr__()


def parse_TM(TM):
    valeurs = {}
    
    TITRES_TM_data = []
    TMS_data = []
    for element in TM:
        if element.tag == 'TITRE_TM':
            TITRE_TM_data = {}

            TITRE_TM_data['debut'] = element.attrib['debut']
            TITRE_TM_data['fin'] = element.attrib['fin']
            TITRE_TM_data['id_'] = element.attrib['id']

            TITRES_TM_data.append(FrozenDict(TITRE_TM_data))
            
        elif element.tag == 'TM':
            TM_data = parse_TM(element)

            TMS_data.append(FrozenDict(TM_data))
            
        else:
            raise ValueError(element.tag)
            
    assert len(TMS_data) <= 1

    valeurs['TITRES_TM'] = tuple(TITRES_TM_data)
    valeurs['TM'] = TMS_data[0] if len(TMS_data) == 1 else None
    
    return valeurs


def parse_article(contenu):
    valeurs = {}

    ARTICLE = ElementTree.fromstring(contenu)
    assert ARTICLE.tag == 'ARTICLE'

    #
    META = ARTICLE[0]
    assert META.tag == 'META'

    ##
    META_COMMUN = META[0]
    assert META_COMMUN.tag == 'META_COMMUN'

    ###
    ID = META_COMMUN[0]
    assert ID.tag == 'ID'
    valeurs['ID'] = ID.text

    id_eli_present = 0
    valeurs['ID_ELI'] = ''
    if META_COMMUN[1].tag == 'ID_ELI':
        id_eli_present = 1
        ID_ELI = META_COMMUN[1]
        valeurs['ID_ELI'] = ID_ELI.text
        
    eli_alias_present = 0
    valeurs['ID_ELI_ALIAS'] = ''
    if META_COMMUN[1 + id_eli_present].tag == 'ELI_ALIAS':
        eli_alias_present = 1
        ELI_ALIAS = META_COMMUN[1 + id_eli_present]
        assert len(list(ELI_ALIAS)) == 1
        ID_ELI_ALIAS = ELI_ALIAS[0]
        assert ID_ELI_ALIAS.tag == 'ID_ELI_ALIAS'
        valeurs['ID_ELI_ALIAS'] = ID_ELI_ALIAS.text
        
    ANCIEN_ID = META_COMMUN[1 + id_eli_present + eli_alias_present]
    assert ANCIEN_ID.tag == 'ANCIEN_ID'
    valeurs['ANCIEN_ID'] = ANCIEN_ID.text

    ORIGINE = META_COMMUN[2 + id_eli_present + eli_alias_present]
    assert ORIGINE.tag == 'ORIGINE'
    valeurs['ORIGINE'] = ORIGINE.text

    URL = META_COMMUN[3 + id_eli_present + eli_alias_present]
    assert URL.tag == 'URL'
    valeurs['URL'] = URL.text

    NATURE = META_COMMUN[4 + id_eli_present + eli_alias_present]
    assert NATURE.tag == 'NATURE'
    valeurs['NATURE'] = NATURE.text

    ##
    META_SPEC = META[1]
    assert META_SPEC.tag == 'META_SPEC'

    ###
    META_ARTICLE = META_SPEC[0]
    assert META_ARTICLE.tag == 'META_ARTICLE'

    ####
    NUM = META_ARTICLE[0]
    assert NUM.tag == 'NUM'
    valeurs['NUM'] = NUM.text

    mcs_art_present = 0
    valeurs['MCS_ART'] = ''
    if META_ARTICLE[1].tag == 'MCS_ART':
        mcs_art_present = 1   
        MCS_ART = META_ARTICLE[1]
        valeurs['MCS_ART'] = MCS_ART.text

    etat_present = 0
    valeurs['ETAT'] = ''
    if META_ARTICLE[1 + mcs_art_present].tag == 'ETAT':
        etat_present = 1   
        ETAT = META_ARTICLE[1 + mcs_art_present]
        valeurs['ETAT'] = ETAT.text
        
    DATE_DEBUT = META_ARTICLE[1 + mcs_art_present + etat_present]
    assert DATE_DEBUT.tag == 'DATE_DEBUT'
    valeurs['DATE_DEBUT'] = DATE_DEBUT.text

    DATE_FIN = META_ARTICLE[2 + mcs_art_present + etat_present]
    assert DATE_FIN.tag == 'DATE_FIN'
    valeurs['DATE_FIN'] = DATE_FIN.text

    TYPE = META_ARTICLE[3 + mcs_art_present + etat_present]
    assert TYPE.tag == 'TYPE'
    valeurs['TYPE'] = TYPE.text

    #
    CONTEXTE = ARTICLE[1]
    assert CONTEXTE.tag == 'CONTEXTE'

    ##
    TEXTE = CONTEXTE[0]
    assert TEXTE.tag == 'TEXTE'
    TEXTE_data = {}
    TEXTE_data['autorite'] = TEXTE.attrib['autorite'] if 'autorite' in TEXTE.attrib else None
    TEXTE_data['cid'] = TEXTE.attrib['cid']
    TEXTE_data['date_publi'] = TEXTE.attrib['date_publi']
    TEXTE_data['date_signature'] = TEXTE.attrib['date_signature']
    TEXTE_data['ministere'] = TEXTE.attrib['ministere'] if 'ministere' in TEXTE.attrib else None
    TEXTE_data['nature'] = TEXTE.attrib['nature']
    TEXTE_data['nor'] = TEXTE.attrib['nor']
    TEXTE_data['num'] = TEXTE.attrib['num']
    valeurs['TEXTE'] = FrozenDict(TEXTE_data)

    ###
    TITRES_TXT_data = []
    TMS_data = []
    for element in TEXTE:
        if element.tag == 'TITRE_TXT':
            TITRE_TXT_data = {}

            TITRE_TXT_data['c_titre_court'] = element.attrib['c_titre_court']
            TITRE_TXT_data['debut'] = element.attrib['debut']
            TITRE_TXT_data['fin'] = element.attrib['fin']
            TITRE_TXT_data['id_txt'] = element.attrib['id_txt']

            TITRES_TXT_data.append(FrozenDict(TITRE_TXT_data))
            
        elif element.tag == 'TM':
            TM_data = parse_TM(element)
            
            TMS_data.append(FrozenDict(TM_data))
            
        else:
            raise ValueError(element.tag)
    
    valeurs['TITRES_TXT'] = tuple(TITRES_TXT_data)
    valeurs['TMS'] = tuple(TMS_data)

    #
    VERSIONS = ARTICLE[2]
    assert VERSIONS.tag == 'VERSIONS'
    
    ##
    VERSIONS_data = []
    for VERSION in VERSIONS:
        assert VERSION.tag == 'VERSION'
        
        VERSION_data = {}
        
        VERSION_data['etat'] = VERSION.attrib['etat']
        
        ###
        LIEN_ART = VERSION[0]
        assert LIEN_ART.tag == 'LIEN_ART'
        
        VERSION_data['debut'] = LIEN_ART.attrib['debut']
        VERSION_data['etat'] = LIEN_ART.attrib['etat']
        VERSION_data['fin'] = LIEN_ART.attrib['fin']
        VERSION_data['id_'] = LIEN_ART.attrib['id']
        VERSION_data['num'] = LIEN_ART.attrib['num']
        VERSION_data['origine'] = LIEN_ART.attrib['origine']
        
        VERSIONS_data.append(FrozenDict(VERSION_data))
    valeurs['VERSIONS'] = frozenset(VERSIONS_data)

    #
    nota_present = 0
    valeurs['NOTA'] = ''
    if ARTICLE[3].tag == 'NOTA':
        nota_present = 1
        NOTA = ARTICLE[3]
        assert len(list(NOTA)) == 1

        ##
        CONTENU = NOTA[0]
        valeurs['NOTA'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')

    #
    sm_present = 0
    valeurs['SM'] = ''
    if ARTICLE[3 + nota_present].tag == 'SM':
        sm_present = 1
        SM = ARTICLE[3 + nota_present]

        ##
        CONTENU = SM[0]
        valeurs['SM'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')

    #
    BLOC_TEXTUEL = ARTICLE[3 + nota_present + sm_present]
    assert BLOC_TEXTUEL.tag == 'BLOC_TEXTUEL'

    ##
    CONTENU = BLOC_TEXTUEL[0]
    valeurs['BLOC_TEXTUEL'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')

    #
    LIENS_data = []
    LIENS = ARTICLE[4 + nota_present + sm_present]
    assert LIENS.tag == 'LIENS'
        
    ##
    for LIEN in LIENS:
        assert LIEN.tag == 'LIEN'

        LIEN_data = {}

        LIEN_data['cidtexte'] = LIEN.attrib['cidtexte']
        LIEN_data['datesignatexte'] = LIEN.attrib['datesignatexte']
        LIEN_data['id_'] = LIEN.attrib['id']
        LIEN_data['naturetexte'] = LIEN.attrib['naturetexte']
        LIEN_data['nortexte'] = LIEN.attrib['nortexte']
        LIEN_data['num'] = LIEN.attrib['num']
        LIEN_data['numtexte'] = LIEN.attrib['numtexte']
        LIEN_data['sens'] = LIEN.attrib['sens']
        LIEN_data['typelien'] = LIEN.attrib['typelien']
        LIEN_data['texte'] = LIEN.text

        LIENS_data.append(FrozenDict(LIEN_data))
    valeurs['LIENS'] = tuple(LIENS_data)

    assert len(ARTICLE) == 5 + nota_present + sm_present

    return valeurs


def parse_un_article(base_origine, categorie, cid, id_):
    if base_origine == 'JORF':
        nom_fichier = os.path.join(racine_jorf, 'article', id_ + '.xml')
    elif base_origine == 'LEGI':
        nom_fichier = os.path.join(racine_legi, categorie, cid, id_ + '.xml')
    else:
        raise ValueError(base_origine)

    with open(nom_fichier) as f:
        contenu = f.read()

    return parse_article(contenu)

