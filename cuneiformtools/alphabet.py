#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Aleksi Sahala 2020 -- Assyriological alphabet definitions """

mixed_uppercase = False # set True to aAbB order instead of abAB

""" Define custom alphabetic order for Assyriological symbols.
If you encounter errors while sorting, add new characters here. """

DELIMITERS = '}{.:-' # includes determinative borders
NONALPHANUMERIC = "×!@#&%–-_[{⸢<()>⸣}].:;',?/\*`~$^+=“⁻ "
ZERO = 'Ø'

## Index defititions =========================================
NUMERIC = "0123456789"      # Numeric indices used in ASCII
INDEX = "₀₁₂₃₄₅₆₇₈₉"            # Subsript indices used in UTF-8
X_NUMERIC = "x"             # Numerix x-index in ASCII
X_INDEX = "ₓ"               # Subscript x-index in UTF-8

## Accented indices (both must be in the same order)
ACUTE = 'áéíúÁÉÍÚ' 
GRAVE = 'àèìùÀÈÌÙ'
PLAIN = 'aeiuAEIU'      # Base for accented vowels

## Map ACUTE and GRAVE accents with PLAIN vowels.
DEACCENT = {s: t for s, t in zip(tuple(ACUTE+GRAVE),
                                 tuple(PLAIN+PLAIN))}


ALEPH = "ʾˀ"
ALPHA = "aáàâābcdeéèêēfgĝŋhḫiíìîījklmnoóòōôpqrřȓsšṣtṭuúùûūvwxyz"
CONSONANT = "bdfgĝŋhḫjklmnpqrřȓsšśṣtṭvwxyz" + ALEPH
VOWEL = "aiueo"
PIPE = "|"
ALPHANUMERIC = ALPHA + NUMERIC
BRACKETS = '[⸢⸣]'
LACUNA_META = '<[⸢⸣]>!?'

ALLNUMBERS = ''.join([j for i in zip(list(NUMERIC),
                                     list(INDEX)) for j in i])

if mixed_uppercase:
    ALLALPHA = ''.join([j for i in zip(list(ALPHA),
                                       list(ALPHA.upper())) for j in i])
else:
    ALLALPHA = ALPHA + ALPHA.upper()
        
ALPHABET = NONALPHANUMERIC + ZERO +\
           ALLNUMBERS + X_INDEX + ALEPH + ALLALPHA + PIPE

""" Define index remover """
INDICES = INDEX + X_INDEX
REMOVE_INDEX = str.maketrans(INDICES, "_"*len(INDICES))

""" Define index ASCIIfier """
ASCII_INDEX = str.maketrans(NUMERIC + X_NUMERIC, INDEX + X_INDEX)
