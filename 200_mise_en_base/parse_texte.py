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


def parse_struct(contenu):
    valeurs = {}
    
    TEXTELR = ElementTree.fromstring(contenu)
    assert TEXTELR.tag == 'TEXTELR'

    #
    META = TEXTELR[0]
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
    META_TEXTE_CHRONICLE = META_SPEC[0]
    assert META_TEXTE_CHRONICLE.tag == 'META_TEXTE_CHRONICLE'

    ####
    CID = META_TEXTE_CHRONICLE[0]
    assert CID.tag == 'CID'
    valeurs['CID'] = CID.text

    NUM = META_TEXTE_CHRONICLE[1]
    assert NUM.tag == 'NUM'
    valeurs['NUM'] = NUM.text

    NUM_SEQUENCE = META_TEXTE_CHRONICLE[2]
    assert NUM_SEQUENCE.tag == 'NUM_SEQUENCE'
    valeurs['NUM_SEQUENCE'] = NUM_SEQUENCE.text

    NOR = META_TEXTE_CHRONICLE[3]
    assert NOR.tag == 'NOR'
    valeurs['NOR'] = NOR.text

    DATE_PUBLI = META_TEXTE_CHRONICLE[4]
    assert DATE_PUBLI.tag == 'DATE_PUBLI'
    valeurs['DATE_PUBLI'] = DATE_PUBLI.text

    DATE_TEXTE = META_TEXTE_CHRONICLE[5]
    assert DATE_TEXTE.tag == 'DATE_TEXTE'
    valeurs['DATE_TEXTE'] = DATE_TEXTE.text

    der_modif_present = 0
    valeurs['DERNIERE_MODIFICATION'] = ''
    if META_TEXTE_CHRONICLE[6].tag == 'DERNIERE_MODIFICATION':
        der_modif_present = 1
        DERNIERE_MODIFICATION = META_TEXTE_CHRONICLE[6]
        valeurs['DERNIERE_MODIFICATION'] = DERNIERE_MODIFICATION.text
    
    versions_a_venir_present = 0
    VERSIONS_A_VENIR_data = []
    if META_TEXTE_CHRONICLE[6 + der_modif_present].tag == 'VERSIONS_A_VENIR':
        versions_a_venir_present = 1
        VERSIONS_A_VENIR = META_TEXTE_CHRONICLE[6 + der_modif_present]
        
        #####
        for VERSION_A_VENIR in VERSIONS_A_VENIR:
            assert VERSION_A_VENIR.tag == 'VERSION_A_VENIR'
            VERSIONS_A_VENIR_data.append(VERSION_A_VENIR.text)
    valeurs['VERSIONS_A_VENIR'] = tuple(VERSIONS_A_VENIR_data)
    
    ORIGINE_PUBLI = META_TEXTE_CHRONICLE[6 + der_modif_present + versions_a_venir_present]
    assert ORIGINE_PUBLI.tag == 'ORIGINE_PUBLI'
    valeurs['ORIGINE_PUBLI'] = ORIGINE_PUBLI.text
    
    PAGE_DEB_PUBLI = META_TEXTE_CHRONICLE[7 + der_modif_present + versions_a_venir_present]
    assert PAGE_DEB_PUBLI.tag == 'PAGE_DEB_PUBLI'
    valeurs['PAGE_DEB_PUBLI'] = PAGE_DEB_PUBLI.text
    
    PAGE_FIN_PUBLI = META_TEXTE_CHRONICLE[8 + der_modif_present + versions_a_venir_present]
    assert PAGE_FIN_PUBLI.tag == 'PAGE_FIN_PUBLI'
    valeurs['PAGE_FIN_PUBLI'] = PAGE_FIN_PUBLI.text

    #
    VERSIONS = TEXTELR[1]
    assert VERSIONS.tag == 'VERSIONS'
    
    ##
    VERSIONS_data = []
    for VERSION in VERSIONS:
        assert VERSION.tag == 'VERSION'
        
        VERSION_data = {}
        
        VERSION_data['etat'] = VERSION.attrib['etat']
        
        ###
        LIEN_TXT = VERSION[0]
        assert LIEN_TXT.tag == 'LIEN_TXT'
        
        VERSION_data['debut'] = LIEN_TXT.attrib['debut']
        VERSION_data['fin'] = LIEN_TXT.attrib['fin']
        VERSION_data['id_'] = LIEN_TXT.attrib['id']
        VERSION_data['num'] = LIEN_TXT.attrib['num']
        
        VERSIONS_data.append(FrozenDict(VERSION_data))
    valeurs['VERSIONS'] = frozenset(VERSIONS_data)
        
    #
    STRUCT = TEXTELR[2]
    assert STRUCT.tag == 'STRUCT'
    
    ##
    LIENS_ART_data = []
    LIENS_SECTION_TA_data = []
    for LIEN in STRUCT:
        if LIEN.tag == 'LIEN_ART':
            LIEN_ART_data = {}

            LIEN_ART_data['debut'] = LIEN.attrib['debut']
            LIEN_ART_data['etat'] = LIEN.attrib['etat']
            LIEN_ART_data['fin'] = LIEN.attrib['fin']
            LIEN_ART_data['id_'] = LIEN.attrib['id']
            LIEN_ART_data['num'] = LIEN.attrib['num']
            LIEN_ART_data['origine'] = LIEN.attrib['origine']

            LIENS_ART_data.append(FrozenDict(LIEN_ART_data))
            
        elif LIEN.tag == 'LIEN_SECTION_TA':
            LIEN_SECTION_TA_data = {}

            LIEN_SECTION_TA_data['cid'] = LIEN.attrib['cid']
            LIEN_SECTION_TA_data['debut'] = LIEN.attrib['debut']
            LIEN_SECTION_TA_data['etat'] = LIEN.attrib['etat']
            LIEN_SECTION_TA_data['fin'] = LIEN.attrib['fin']
            LIEN_SECTION_TA_data['id_'] = LIEN.attrib['id']
            LIEN_SECTION_TA_data['niv'] = LIEN.attrib['niv']
            LIEN_SECTION_TA_data['url'] = LIEN.attrib['url']

            LIENS_SECTION_TA_data.append(FrozenDict(LIEN_SECTION_TA_data))
            
        else:
            raise ValueError(LIEN.tag)
    valeurs['LIENS_ART'] = tuple(LIENS_ART_data)
    valeurs['LIENS_SECTION_TA'] = tuple(LIENS_SECTION_TA_data)

    return valeurs


def parse_version(contenu):
    valeurs = {}
    
    TEXTE_VERSION = ElementTree.fromstring(contenu)
    assert TEXTE_VERSION.tag == 'TEXTE_VERSION'

    #
    META = TEXTE_VERSION[0]
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
    META_TEXTE_CHRONICLE = META_SPEC[0]
    assert META_TEXTE_CHRONICLE.tag == 'META_TEXTE_CHRONICLE'

    ####
    CID = META_TEXTE_CHRONICLE[0]
    assert CID.tag == 'CID'
    valeurs['CID'] = CID.text

    NUM = META_TEXTE_CHRONICLE[1]
    assert NUM.tag == 'NUM'
    valeurs['NUM'] = NUM.text

    NUM_SEQUENCE = META_TEXTE_CHRONICLE[2]
    assert NUM_SEQUENCE.tag == 'NUM_SEQUENCE'
    valeurs['NUM_SEQUENCE'] = NUM_SEQUENCE.text

    NOR = META_TEXTE_CHRONICLE[3]
    assert NOR.tag == 'NOR'
    valeurs['NOR'] = NOR.text

    DATE_PUBLI = META_TEXTE_CHRONICLE[4]
    assert DATE_PUBLI.tag == 'DATE_PUBLI'
    valeurs['DATE_PUBLI'] = DATE_PUBLI.text

    DATE_TEXTE = META_TEXTE_CHRONICLE[5]
    assert DATE_TEXTE.tag == 'DATE_TEXTE'
    valeurs['DATE_TEXTE'] = DATE_TEXTE.text

    der_modif_present = 0
    valeurs['DERNIERE_MODIFICATION'] = ''
    if META_TEXTE_CHRONICLE[6].tag == 'DERNIERE_MODIFICATION':
        der_modif_present = 1
        DERNIERE_MODIFICATION = META_TEXTE_CHRONICLE[6]
        valeurs['DERNIERE_MODIFICATION'] = DERNIERE_MODIFICATION.text
    
    versions_a_venir_present = 0
    VERSIONS_A_VENIR_data = []
    if META_TEXTE_CHRONICLE[6 + der_modif_present].tag == 'VERSIONS_A_VENIR':
        versions_a_venir_present = 1
        VERSIONS_A_VENIR = META_TEXTE_CHRONICLE[6 + der_modif_present]
        
        #####
        for VERSION_A_VENIR in VERSIONS_A_VENIR:
            assert VERSION_A_VENIR.tag == 'VERSION_A_VENIR'
            VERSIONS_A_VENIR_data.append(VERSION_A_VENIR.text)
    valeurs['VERSIONS_A_VENIR'] = tuple(VERSIONS_A_VENIR_data)
    
    ORIGINE_PUBLI = META_TEXTE_CHRONICLE[6 + der_modif_present + versions_a_venir_present]
    assert ORIGINE_PUBLI.tag == 'ORIGINE_PUBLI'
    valeurs['ORIGINE_PUBLI'] = ORIGINE_PUBLI.text
    
    PAGE_DEB_PUBLI = META_TEXTE_CHRONICLE[7 + der_modif_present + versions_a_venir_present]
    assert PAGE_DEB_PUBLI.tag == 'PAGE_DEB_PUBLI'
    valeurs['PAGE_DEB_PUBLI'] = PAGE_DEB_PUBLI.text
    
    PAGE_FIN_PUBLI = META_TEXTE_CHRONICLE[8 + der_modif_present + versions_a_venir_present]
    assert PAGE_FIN_PUBLI.tag == 'PAGE_FIN_PUBLI'
    valeurs['PAGE_FIN_PUBLI'] = PAGE_FIN_PUBLI.text

    ###
    META_TEXTE_VERSION = META_SPEC[1]
    assert META_TEXTE_VERSION.tag == 'META_TEXTE_VERSION'

    ####
    TITRE = META_TEXTE_VERSION[0]
    assert TITRE.tag == 'TITRE'
    valeurs['TITRE'] = TITRE.text

    TITREFULL = META_TEXTE_VERSION[1]
    assert TITREFULL.tag == 'TITREFULL'
    valeurs['TITREFULL'] = TITREFULL.text

    etat_present = 0
    valeurs['ETAT'] = ''
    if META_TEXTE_VERSION[2].tag == 'ETAT':
        etat_present = 1   
        ETAT = META_TEXTE_VERSION[2]
        valeurs['ETAT'] = ETAT.text

    DATE_DEBUT = META_TEXTE_VERSION[2 + etat_present]
    assert DATE_DEBUT.tag == 'DATE_DEBUT'
    valeurs['DATE_DEBUT'] = DATE_DEBUT.text

    DATE_FIN = META_TEXTE_VERSION[3 + etat_present]
    assert DATE_FIN.tag == 'DATE_FIN'
    valeurs['DATE_FIN'] = DATE_FIN.text

    AUTORITE = META_TEXTE_VERSION[4 + etat_present]
    assert AUTORITE.tag == 'AUTORITE'
    valeurs['AUTORITE'] = AUTORITE.text

    MINISTERE = META_TEXTE_VERSION[5 + etat_present]
    assert MINISTERE.tag == 'MINISTERE'
    valeurs['MINISTERE'] = MINISTERE.text

    mcs_txt_present = 0
    valeurs['MCS_TXT'] = ''
    if (len(META_TEXTE_VERSION) >= 7 + etat_present) and (META_TEXTE_VERSION[6 + etat_present].tag == 'MCS_TXT'):
        mcs_txt_present = 1   
        MCS_TXT = META_TEXTE_VERSION[6 + etat_present]
        valeurs['MCS_TXT'] = MCS_TXT.text
    
    liens_present = 0
    LIENS_data = []
    if len(META_TEXTE_VERSION) == 7 + etat_present + mcs_txt_present:
        liens_present = 1
        LIENS = META_TEXTE_VERSION[6 + etat_present + mcs_txt_present]
        assert LIENS.tag == 'LIENS'
        
        #####
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

    assert len(META_TEXTE_VERSION) == 6 + etat_present + mcs_txt_present + liens_present

    #
    notice_present = 0
    valeurs['NOTICE'] = ''
    if TEXTE_VERSION[1].tag == 'NOTICE':
        notice_present = 1
        NOTICE = TEXTE_VERSION[1]

        ##
        CONTENU = NOTICE[0]
        valeurs['NOTICE'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')

    
    #
    VISAS = TEXTE_VERSION[1 + notice_present]
    assert VISAS.tag == 'VISAS'

    ##
    CONTENU = VISAS[0]
    valeurs['VISAS'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')
      
    #
    SIGNATAIRES = TEXTE_VERSION[2 + notice_present]
    assert SIGNATAIRES.tag == 'SIGNATAIRES'

    ##
    CONTENU = SIGNATAIRES[0]
    valeurs['SIGNATAIRES'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')
      
    #
    TP = TEXTE_VERSION[3 + notice_present]
    assert TP.tag == 'TP'

    ##
    CONTENU = TP[0]
    valeurs['TP'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')
      
    #
    nota_present = 0
    valeurs['NOTA'] = ''
    if TEXTE_VERSION[4 + notice_present].tag == 'NOTA':
        nota_present = 1
        NOTA = TEXTE_VERSION[4 + notice_present]

        ##
        CONTENU = NOTA[0]
        valeurs['NOTA'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')
      
    #
    ABRO = TEXTE_VERSION[4 + notice_present + nota_present]
    assert ABRO.tag == 'ABRO'

    ##
    CONTENU = ABRO[0]
    valeurs['ABRO'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')
      
    #
    RECT = TEXTE_VERSION[5 + notice_present + nota_present]
    assert RECT.tag == 'RECT'

    ##
    CONTENU = RECT[0]
    valeurs['RECT'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')
            
    #
    sm_present = 0
    valeurs['SM'] = ''
    assert len(TEXTE_VERSION) in [6 + notice_present + nota_present, 7 + notice_present + nota_present]
    if len(TEXTE_VERSION) == 7 + notice_present + nota_present:
        sm_present = 1
        SM = TEXTE_VERSION[6 + notice_present + nota_present]

        ##
        CONTENU = SM[0]
        valeurs['SM'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')
            
    return valeurs


def parse_cid(cid, curseur):
    curseur.execute("select base_origine, categorie, cid, id_ from struct where valide = True and cid = %s;",
                    (cid,))
    liste_struct = curseur.fetchall()
    
    curseur.execute("select base_origine, categorie, cid, id_ from version where valide = True and cid = %s;",
                    (cid,))
    liste_version = curseur.fetchall()
    
    assert len(liste_struct) == len(liste_version)
    assert sorted([l[3] for l in liste_struct]) == sorted([l[3] for l in liste_struct])
    liste_id_ = [l[3] for l in liste_struct]
    assert len(liste_id_) == len(set(liste_id_))
    assert cid in liste_id_
    
    valeurs_struct_par_id_ = {}
    for base_origine, categorie, cid, id_ in liste_struct:
        if base_origine == 'JORF':
            nom_fichier = os.path.join(racine_jorf, 'texte/struct', id_ + '.xml')
        elif base_origine == 'LEGI':
            nom_fichier = os.path.join(racine_legi, categorie, cid, 'struct', id_ + '.xml')
        else:
            raise ValueError(base_origine)

        with open(nom_fichier) as f:
            contenu = f.read()

        valeurs_struct = parse_struct(contenu)
        valeurs_struct_par_id_[id_] = valeurs_struct

    valeurs_version_par_id_ = {}
    for base_origine, categorie, cid, id_ in liste_version:
        if base_origine == 'JORF':
            nom_fichier = os.path.join(racine_jorf, 'texte/version', id_ + '.xml')
        elif base_origine == 'LEGI':
            nom_fichier = os.path.join(racine_legi, categorie, cid, 'version', id_ + '.xml')
        else:
            raise ValueError(base_origine)

        with open(nom_fichier) as f:
            contenu = f.read()
        valeurs_version = parse_version(contenu)
        valeurs_version_par_id_[id_] = valeurs_version

    
    return liste_id_, valeurs_struct_par_id_, valeurs_version_par_id_


infos_communes = [
    'ID_ELI',
    'ID_ELI_ALIAS',
    'NATURE',
    'CID',
    'NUM',
    'NUM_SEQUENCE',
    'NOR',
    'DATE_PUBLI',
    'DATE_TEXTE',
    'DERNIERE_MODIFICATION',
    'VERSIONS_A_VENIR',
    'ORIGINE_PUBLI',
    'PAGE_DEB_PUBLI',
    'PAGE_FIN_PUBLI',
]

infos_communes_struct = [
    'VERSIONS',
]

infos_communes_version = [
    'AUTORITE',
    'MINISTERE',
]

infos_particulieres = [
    'ID',
    'ANCIEN_ID',
    'ORIGINE'
]

infos_particulieres_struct = [
    'URL',
    'LIENS_ART',
    'LIENS_SECTION_TA',
]

infos_particulieres_version = [
    'URL',
    'TITRE',
    'TITREFULL',
    'ETAT',    
    'DATE_DEBUT',
    'DATE_FIN',
    'MCS_TXT',
    'LIENS',
    'NOTICE',
    'VISAS',
    'SIGNATAIRES',
    'TP',
    'NOTA',
    'ABRO',
    'RECT',
    'SM',
]
