import re
from collections import Counter

""" Transliteration and lemmatization normalizer :: asahala 2021

This script normalizes inconsistencies in Oracc transliteration.
XLITTools has the following methods:

  accent_to_index(string)
             Normalizes accented indices into unicode
             subscript numbers.

  unify_determinatives(string)
             Normalize determinatives into uppercase. There are
             lots of dubious phonetic complements in Oracc not
             properly marked with precding +, these are not
             separated here. Korp Oracc version has also bugged
             phonetic complements with missing hyphens.

  normalize_h(string)
             Removes diacritic from /h/.

  normalize_all(string)
             Apply all normalizations to string if they are
             relevant to it.


LemmaTools can be used to fix some incosistencies in Oracc
lemmatization.
             
"""

LOG = []

def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read().splitlines()

def save_log(filename):
    if LOG:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('total changes: %i\n' % len(LOG))
            f.write('number\tchange\n')
            for entry, num in sorted(Counter(LOG).items()):
                f.write('%s\t%s\n' % (str(num), entry))
        print('> %i normalizations made, see %s' % (len(LOG), filename))
    else:
        print('Log is empty!')

def logger(orig, fix, id_=None):
    """ Collect all changes into log """
    if id_ is None:
        identifier = '_'
    else:
        identifier = id_
        
    if orig != fix:
        LOG.append('%s\t%s -> %s' % (identifier, orig, fix))


class XLITTools:

    def __init__(self):
        self.two = frozenset('áéíúÁÉÍÚ')
        self.three = frozenset('àèìùÀÈÌÙ')
        self.accents = self.two.union(self.three)
        self.deaccent = {'à': 'a', 'á': 'a',
                         'è': 'e', 'é': 'e',
                         'ì': 'i', 'í': 'i',
                         'ù': 'u', 'ú': 'u',
                         'À': 'A', 'Á': 'A',
                         'È': 'E', 'É': 'E',
                         'Ì': 'I', 'Í': 'I',
                         'Ù': 'U', 'Ú': 'U'}
        self.split = frozenset('.-– ×{}*?!()\t')
        self.h = str.maketrans('ḫḪ', 'hH')

    def accent_to_index(self, string):
        xlit = ''
        index = ''
        for c in string + ' ':
            if c in self.two:
                index = '₂'
            if c in self.three:
                index = '₃'
            if c in self.split:
                xlit += index + c
                index = ''
            else:
                xlit += self.deaccent.get(c, c)
        xlit = re.sub('([⌉\]>])([₂₃])', r'\2\1', xlit)
        return xlit.rstrip()

    def unify_determinatives(self, string):
        norm = ''
        # This is safe substitution and does not conflict
        # with anything
        string = string.replace('d.', '{d}')
        if '{' in string:
            upper = False
            i = 0
            for c in string:
                if c == '{':
                    upper = True
                elif c == '+' and string[i-1] == '{':
                    upper = False
                elif c == '}':
                    upper = False
                elif c in ('m', 'd', 'f', '1')\
                     and string[i-1] == '{' and string[i+1] == '}':
                    upper = False
                    if c == '1':
                        c = 'm'
                if upper:
                    c = c.upper() ## change into lowercase instead, FIX
                norm += c
                i += 1
            string = norm
        return string

    def normalize_h(self, string):
        norm = string.translate(self.h)
        return norm
    
    def normalize_all(self, string, id_=None):
        norm = self.normalize_h(string)
        chars = set(norm)
        if id_ == 'xlit':
            if chars.intersection(self.accents):
                norm = self.accent_to_index(norm)
            if '{' in norm or 'd.' in norm:
                norm = self.unify_determinatives(norm)
        logger(string, norm, id_)
        return norm


class LemmaTools:

    def __init__(self, errorfile=None):
        self.fixdict = {}
        if errorfile is not None:
            self.make_dict(errorfile)

    def make_dict(self, filename):
        """ Initialize stuff to be corrected """
        for line in read_file(filename):
            if not line.startswith('#'):
                error, correct, pos = line.split('\t')
                self.fixdict[error + '+' + pos] = correct

    def fix_lemma(self, lemma, pos):
        key = '%s+%s' % (lemma, pos)
        norm = self.fixdict.get(key, lemma)
        logger(lemma, norm, 'lemma')
        return norm
