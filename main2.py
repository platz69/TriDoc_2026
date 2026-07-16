import unicodedata
mot = 'françaisl''été'
mot_sans_accent = ''.join(c for c in unicodedata.normalize('NFD', mot) if unicodedata.category(c) != 'Mn')
print(mot_sans_accent)