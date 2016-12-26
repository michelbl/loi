#!/bin/false

# déplacer les fichiers
find . -type f -exec mv -n \{\} ~/jorf_plat/article \;
find . -type f -exec mv -n \{\} ~/jorf_plat/conteneur \;
find . -type f -exec mv -n \{\} ~/jorf_plat/section_ta \;
find . -type f -exec mv -n \{\} ~/jorf_plat/texte/struct \;
find . -type f -exec mv -n \{\} ~/jorf_plat/texte/version \;

# vérifier qu'il ne reste plus de fichier
find . -type f

# supprimer les dossiers vides (executer plusieurs fois)
find . -type d -exec rmdir \{\} \;
