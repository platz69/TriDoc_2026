# TriDoc 2026

Outil d'organisation et classification automatique de fichiers PDF basé sur l'extraction et l'analyse de texte.

## Fonctionnalités

- **Extraction de texte** : Lit le contenu des PDFs avec normalization des caractères spéciaux et ligatures
- **Filtrage intelligent** : Utilise un dictionnaire français pour identifier les mots-clés pertinents
- **Détection par patterns** : Complète l'extraction par des expressions régulières personnalisables (codes, numéros, etc.)
- **Exclusions** : Maintient une liste de mots à ignorer (noms personnels, mots vides, etc.)
- **Rangement automatique** : Classe et déplace les PDFs dans des dossiers basés sur les mots-clés détectés
- **Configuration adaptative** : Permet d'ajouter interactivement de nouveaux mots-clés et dossiers de rangement
- **Persistance** : Sauvegarde le mapping mot-clé → dossier et la liste d'exclusion

## Installation

```bash
# Cloner le projet
git clone https://github.com/platz69/TriDoc_2026.git
cd TriDoc_2026

# Créer un environnement virtuel (recommandé)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install pypdf unicodedata  # unicodedata est built-in, pypdf requis
```

## Prérequis

- Python 3.8+
- `pypdf` : Extraction de texte depuis PDFs
- Fichiers de configuration :
  - `French.dic` : Dictionnaire français (mots valides)
  - `Mots_a_exclure.dic` : Mots à ignorer
  - `Rangement.csv` : Mapping mot-clé → dossier (généré automatiquement)

## Usage

```bash
python main.py
```

### Flux de traitement

Pour chaque PDF dans le répertoire configuré :

1. **Extraction** : Extrait le texte de toutes les pages
2. **Filtrage** : Identifie les mots pertinents selon les critères :
   - Pas dans le dictionnaire français
   - Pas dans la liste d'exclusion
   - Longueur > 2 caractères
   - Pas de chiffres < 5 caractères
   - Pas de caractères répétés (> 4 fois)
   - Pas de points aux extrémités
3. **Détection regex** : Applique les patterns définis dans `REGEX_PATTERNS`
4. **Rangement** :
   - Automatique si un mot-clé du CSV est trouvé
   - Interactif : propose les mots détectés à l'utilisateur
   - Création de nouveau dossier/mot-clé si nécessaire
5. **Persistance** : Sauvegarde les nouvelles associations et exclusions

## Configuration

### Répertoire de travail

Modifier `REPERTOIRE` dans le bloc `if __name__ == "__main__"` :

```python
REPERTOIRE = r"C:\Users\...\Downloads\PDF_Tests"
```

### Fichiers de configuration

| Fichier | Format | Description |
|---------|--------|-------------|
| `French.dic` | Un mot par ligne | Dictionnaire français complet |
| `Mots_a_exclure.dic` | Un mot par ligne | Mots à ignorer (noms, adresses, etc.) |
| `Rangement.csv` | `mot-clé;chemin_dossier` | Mapping mot-clé → dossier destination |

### Patterns regex (optionnel)

Ajouter des expressions régulières dans `REGEX_PATTERNS` pour détecter des motifs spécifiques :

```python
REGEX_PATTERNS: list = [
    r'\b\d{5}\b',              # Codes postaux (5 chiffres)
    r'\b[A-Z]{2,}\b',          # Sigles (majuscules > 2 chars)
    r'SIRET[:\s]+\d{14}',      # Numéros SIRET
    r'SIREN[:\s]+\d{9}',       # Numéros SIREN
]
```

## Exemple de flux utilisateur

```
Fichier : C:\Users\platz69\Downloads\PDF_Tests\document.pdf

[page 1] Texte extrait...
[page 2] Texte extrait...

['cgi', 'facture', 'montant', 'remboursement', ...]

Détectés (regex) : ['69003', 'SIREN123456789']

Mot-clé pour rangement (ou Entrée pour passer) : cgi
✓ PDF déplacé vers : C:\Users\...\Downloads\PDF_Tests\...\document.pdf

Ajouter des mots à exclure séparés par des virgules (ou Entrée pour passer) : 
```

## Structure du code

- `charger_un_dictionnaire()` : Charge un fichier texte en set
- `charger_rangement()` : Parse le CSV de rangement
- `convertir_diacritiques()` : Normalise les caractères accentués
- `traiter_pdf()` : Cœur du traitement (extraction, filtrage, rangement)
- `verifier_et_deplacer_pdf()` : Déplace le PDF si rangement trouvé
- `est_nom_dossier_valide()` : Vérifie les caractères interdits Windows
- `sauvegarder_rangement()` : Persiste le mapping mot-clé → dossier
- `sauvegarder_mots_a_exclure()` : Persiste la liste d'exclusion
