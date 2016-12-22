import psycopg2
import xml.etree.ElementTree as ElementTree
import sys

repertoire_racine = '/home/michel/jorf_plat/'
version_courante = '8'
assert len(sys.argv) == 3
nb_proc = int(sys.argv[1])
id_proc = int(sys.argv[2])

def parse_contenu(contenu):
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
    assert ORIGINE.text == 'JORF'

    URL = META_COMMUN[3 + id_eli_present + eli_alias_present]
    assert URL.tag == 'URL'
    valeurs['URL'] = URL.text

    NATURE = META_COMMUN[4 + id_eli_present + eli_alias_present]
    assert NATURE.tag == 'NATURE'
    assert NATURE.text == 'Article'

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

    MCS_ART = META_ARTICLE[1]
    assert MCS_ART.tag == 'MCS_ART'
    valeurs['MCS_ART'] = MCS_ART.text

    DATE_DEBUT = META_ARTICLE[2]
    assert DATE_DEBUT.tag == 'DATE_DEBUT'
    valeurs['DATE_DEBUT'] = DATE_DEBUT.text

    DATE_FIN = META_ARTICLE[3]
    assert DATE_FIN.tag == 'DATE_FIN'
    valeurs['DATE_FIN'] = DATE_FIN.text

    TYPE = META_ARTICLE[4]
    assert TYPE.tag == 'TYPE'
    valeurs['TYPE'] = TYPE.text

    #
    CONTEXTE = ARTICLE[1]
    assert CONTEXTE.tag == 'CONTEXTE'

    ##
    TEXTE = CONTEXTE[0]
    assert TEXTE.tag == 'TEXTE'
    valeurs['TEXTE_cid'] = TEXTE.attrib['cid'] # des infos sont ignorées

    #
    VERSIONS = ARTICLE[2]
    assert VERSIONS.tag == 'VERSIONS'

    ## ignore les versions
    #assert len(list(VERSIONS)) == 1
    #VERSION = VERSIONS[0]
    #assert VERSION.tag == 'VERSION'
    #assert VERSION.attrib['etat'] == ''

    ###
    #LIEN_ART = VERSION[0]
    #assert LIEN_ART.tag == 'LIEN_ART'
    #assert LIEN_ART.attrib['debut'] == '2999-01-01'
    #assert LIEN_ART.attrib['fin'] == '2999-01-01'
    #assert LIEN_ART.attrib['etat'] == ''
    #assert LIEN_ART.attrib['id'] == valeurs['ID']
    #valeurs['VERSION_NUM'] = LIEN_ART.attrib['num']
    #assert LIEN_ART.attrib['origine'] == 'JORF'

    #
    SM = ARTICLE[3]
    assert SM.tag == 'SM'

    ##
    assert len(list(SM)) == 1
    CONTENU = SM[0]
    assert CONTENU.tag == 'CONTENU'

    ###
    assert len(list(CONTENU)) == 0
    assert CONTENU.text is None

    #
    BLOC_TEXTUEL = ARTICLE[4]
    assert BLOC_TEXTUEL.tag == 'BLOC_TEXTUEL'

    ##
    CONTENU = BLOC_TEXTUEL[0]
    valeurs['BLOC_TEXTUEL'] = ElementTree.tostring(CONTENU, encoding='unicode', method='xml')

    #
    LIENS = ARTICLE[5]
    assert LIENS.tag == 'LIENS'

    ##
    assert len(list(LIENS)) == 0
    
    return valeurs


connection = psycopg2.connect(dbname='jorf', user='jorf', password='baba')
curseur = connection.cursor()

while True:
    curseur.execute("select * from article where (status is null or status != %s) and (mod(numero_ligne, %s) = %s) limit 1;", (version_courante, nb_proc, id_proc))
    resultat_requete = curseur.fetchone()
    
    if not resultat_requete:
        break
        
    nom_fichier = resultat_requete[0]
        
    with open(repertoire_racine + 'article/' + nom_fichier) as f:
        contenu = f.read()
    
    valeurs = parse_contenu(contenu)
    
    valeurs['status'] = version_courante
    valeurs['nom_fichier'] = nom_fichier

    curseur.execute("""
        update article set
            ID = %(ID)s,
            ID_ELI = %(ID_ELI)s,
            ID_ELI_ALIAS = %(ID_ELI_ALIAS)s,
            ANCIEN_ID = %(ANCIEN_ID)s,
            MCS_ART = %(MCS_ART)s,
            NUM = %(NUM)s,
            TYPE = %(TYPE)s,
            URL = %(URL)s,
            TEXTE_cid = %(TEXTE_cid)s,
            BLOC_TEXTUEL = %(BLOC_TEXTUEL)s,
            DATE_DEBUT = %(DATE_DEBUT)s,
            DATE_FIN = %(DATE_FIN)s,
            status = %(status)s
        where nom_fichier = %(nom_fichier)s;
        """, valeurs)
    connection.commit()


curseur.close()
connection.close()
