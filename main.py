from pathlib import Path
import unicodedata
from pypdf import PdfReader
import re


def charger_un_dictionnaire(fichier: str) -> set:
    """Charge un fichier dictionnaire et retourne l'ensemble des mots."""
    with open(fichier, "r", encoding="utf-8", errors="ignore") as f:
        mots = set(f.read().splitlines())
    return mots


def charger_rangement(fichier: str) -> dict:
    """Charge le fichier de rangement (CSV à 2 colonnes) et retourne un dictionnaire mot-clé → dossier."""
    donnees = {}
    if Path(fichier).exists():
        with open(fichier, "r", encoding="utf-8", errors="ignore") as f:
            for ligne in f:
                parties = ligne.strip().split(";")
                if len(parties) == 2:
                    mot_cle, chemin = parties
                    donnees[mot_cle.strip()] = chemin.strip()
    return donnees


def convertir_diacritiques(mot: str) -> str:
    """Supprime les accents et diacritiques d'un mot."""
    return ''.join(c for c in unicodedata.normalize('NFD', mot) if unicodedata.category(c) != 'Mn')


def verifier_et_deplacer_pdf(fichier_pdf: Path, mots_cles_possibles: set) -> bool:
    """Vérifie si un mot-clé du rangement est dans les mots détectés et déplace le PDF si trouvé."""
    for mot_cle_csv, dossier_rangement in rangement.items():
        if mot_cle_csv in mots_cles_possibles:
            chemin_dossier = Path(dossier_rangement)
            chemin_dossier.mkdir(parents=True, exist_ok=True)
            chemin_destination = chemin_dossier / fichier_pdf.name
            fichier_pdf.rename(chemin_destination)
            print(f"\033[92m✓ PDF déplacé vers : {chemin_destination}\033[0m")
            return True
    return False


def est_nom_dossier_valide(nom: str) -> bool:
    """Vérifie qu'un nom de dossier ne contient pas de caractères interdits."""
    return not any(char in nom for char in r'<>:"/\|?*')


def traiter_pdf(fichier_pdf: Path) -> None:
    """Traite un fichier PDF : extrait le texte, identifie les mots-clés et propose un rangement."""
    global rangement # à déclarer, car on va le modifier dans cette fonction
    print(f"\033[92mFichier : {fichier_pdf}\033[0m")
    mots_cles_detectes  = set()  # résultats des regex (REGEX_PATTERNS)
    mots_cles_possibles = set()  # autres chaînes de texte susceptibles d'être des mots-clés

    try:
        reader = PdfReader(fichier_pdf)

        # lecture du PDF
        for numero, page in enumerate(reader.pages, start=1):
            texte = page.extract_text()
            if texte:
                texte = unicodedata.normalize("NFKC", texte) # sinon on obtient des ligatures comme le caractère 'ﬁ' au lieu de 'fi'
                mots = re.findall(r"[-@.\w]+", texte, flags=re.UNICODE)

                # détection par expressions régulières définies dans REGEX_PATTERNS
                for pattern in REGEX_PATTERNS:
                    mots_cles_detectes.update(re.compile(REGEX_PATTERNS[pattern], re.IGNORECASE).findall(texte))

                # on ajoute les mots validant plusieurs critères
                mots_cles_possibles.update({
                    mot for mot in mots
                    if (
                            convertir_diacritiques(mot.lower()) not in dictionnaire_global
                            and convertir_diacritiques(mot.lower()) not in mots_a_exclure
                            and not (mot.isdigit() and len(mot) < 5)            # pas moins de 5 chiffres
                            and len(mot) > 2                                    # plus de 2 lettres
                            and not (len(set(mot)) == 1 and len(mot) > 4)       # pas plus de 4 caractères identiques uniquement
                            and not (mot.startswith(".") or mot.endswith("."))  # pas de point aux extrémités
                    )
                })
            else:
                print("\033[93m[Aucun texte détecté sur cette page]\033[0m")

        # vérification automatique du rangement selon le CSV (sensibiité à la casse)
        if not verifier_et_deplacer_pdf(fichier_pdf, mots_cles_possibles):
            # choix d'un mot-clé par l'utilisateur puis rajout
            if mots_cles_detectes:
                print("\033[95mDétectés (regex) :", sorted(mots_cles_detectes), "\033[0m")
            if mots_cles_possibles:
                print(sorted(mots_cles_possibles))
                mot_cle = input("\033[96mMot-clé pour rangement (ou Entrée pour passer) : \033[0m").strip()
                if mot_cle:
                    if mot_cle in rangement:
                        print(f"\033[93m⚠️  Le mot-clé '{mot_cle}' existe déjà dans le rangement !\033[0m")
                    else:
                        # demander le nom du dossier
                        nom_dossier = ""
                        while not nom_dossier or not est_nom_dossier_valide(nom_dossier):
                            nom_dossier = input("\033[96mNom du dossier : \033[0m").strip()
                            if not nom_dossier:
                                print("\033[91m✗ Le nom du dossier ne peut pas être vide\033[0m")
                            elif not est_nom_dossier_valide(nom_dossier):
                                print("\033[91m✗ Caractères interdits : < > : \" / \\ | ? *\033[0m")
                        
                        chemin_dossier = Path(REPERTOIRE) / nom_dossier
                        chemin_dossier.mkdir(exist_ok=True)
                        rangement[mot_cle.lower()] = str(chemin_dossier)
                        sauvegarder_rangement(rangement)
                        verifier_et_deplacer_pdf(fichier_pdf, mots_cles_possibles)
                
                # proposition d'ajouter des mots interdits
                mots_saisis = input("\033[96mAjouter des mots à exclure séparés par des virgules (ou Entrée pour passer) : \033[0m").strip()
                if mots_saisis:
                    mots_a_ajouter = {mot.strip().lower() for mot in mots_saisis.split(",") if mot.strip()}
                    mots_a_exclure.update(mots_a_ajouter)
                    print(f"\033[92m✓ {len(mots_a_ajouter)} mot(s) ajouté(s) à la liste d'exclusion\033[0m")

    except Exception as e:
        print(f"\033[91mErreur lors de la lecture : {e}\033[0m")


def sauvegarder_rangement(donnees: dict) -> None:
    """Sauvegarde le dictionnaire de rangement dans un fichier CSV (format : mot-clé;chemin)."""
    with open(FICHIER_RANGEMENT, "w", encoding="utf-8") as f:
        for mot_cle, chemin in donnees.items():
            f.write(f"{mot_cle};{chemin}\n")


def sauvegarder_mots_a_exclure(donnees: set) -> None:
    """Sauvegarde l'ensemble des mots à exclure dans un fichier (un mot par ligne)."""
    with open(FICHIER_EXCLURE, "w", encoding="utf-8") as f:
        for mot in sorted(donnees):
            f.write(f"{mot}\n")


if __name__ == "__main__":
    FICHIER_DICTIONNAIRE = r"French.dic"
    FICHIER_EXCLURE      = r"Mots_a_exclure.dic"
    FICHIER_RANGEMENT    = r"Rangement.csv"
    REPERTOIRE           = r"C:\Users\thomas.platz\Downloads\PDF_Tests"
    REGEX_PATTERNS = {
        "address": r"(?:\d{1,5}(?: (?:bis|ter))?,? )?(?:avenue|bd|boulevard|chemin|cours|impasse|rue) ['.0-9A-Za-zÀ-ÖØ-öø-ÿ- ]+",
        "cp":      r"(?:\d{4,5})\\h*[A-Za-zÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸàâäçéèêëîïôöùûüÿ]+(?:[\t ]+cedex\\h*\d+)?",
        "iban":    r"[A-Z]{2}\d{2}\\h?(?:\d{4}\\h?){2}\d{2}\\h?[0-9]{2}\\h?(?:[0-9]{4}\\h?){2}[0-9]+",
        "mail":    r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,6}",
        "tel":     r"(?:0|\+\d{2,3} |\+\d{2,3} \(0\) ?)\d(?:[-_. ]?\d{2}){4}",
        "web":     r"(?:https?://|www\.)[a-zA-Z0-9.-]+\.[a-z]{2,6}"
    }

    """à part le répertoire, tout sera stocké en minuscule"""
    dictionnaire_francais          = charger_un_dictionnaire(FICHIER_DICTIONNAIRE)
    dictionnaire_sans_diacritiques = {convertir_diacritiques(mot.lower()) for mot in dictionnaire_francais}
    dictionnaire_global            = dictionnaire_francais | dictionnaire_sans_diacritiques
    mots_a_exclure                 = charger_un_dictionnaire(FICHIER_EXCLURE)
    rangement                      = charger_rangement(FICHIER_RANGEMENT)

    for pdf in Path(REPERTOIRE).glob("*.pdf"):
        traiter_pdf(pdf)

    sauvegarder_mots_a_exclure(mots_a_exclure)
    sauvegarder_rangement(rangement)