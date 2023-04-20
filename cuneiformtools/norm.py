import re
from collections import Counter
from functools import lru_cache
import cuneiformtools.util as util
from cuneiformtools.alphabet import NUMERIC, INDEX, X_NUMERIC,\
     X_INDEX, ACUTE, GRAVE, DEACCENT

""" Transliteration and lemmatization normalizer :: asahala 2021

                                         Version 2022-03-03 (ct)

This script normalizes inconsistencies in Oracc transliteration.
XLITTools has the following methods:

  accent_to_index(string)
             Normalizes accented indices into unicode
             subscript numbers.
             
  unify_determinatives(string, lower)
             Normalize determinatives into uppercase. There are
             lots of dubious phonetic complements in Oracc not
             properly marked with precding +, these are not
             separated here. Korp Oracc version has also bugged
             phonetic complements with missing hyphens.

             Set `lower` to False if you want to have them in
             the upper case

  subscribe_indices(string)
             Converts numeric indices into subcripts, e.g.
             du11 --> du₁₁
             
  normalize_h(string)
             Removes diacritic from /h/.

  normalize_g(string)
             Changes /ĝ/ into /ŋ/.
             
             
  normalize_all(string)
             Apply all normalizations to string if they are
             relevant to it.
             
"""

LOG = []

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


def purge_log():
    LOG = []

def _logger(orig, fix, id_=None):
    """ Collect all changes into log """
    if id_ is None:
        identifier = '_'
    else:
        identifier = id_
        
    if orig != fix:
        LOG.append('%s\t%s -> %s' % (identifier, orig, fix))


class Harmonizer:

    def __init__(self):
        self.two = frozenset(ACUTE)
        self.three = frozenset(GRAVE)
        self.accents = self.two.union(self.three)
        self.numbers = frozenset(NUMERIC+X_NUMERIC)
        self.deaccent = DEACCENT
        self.split = frozenset('.-– ×{}*?!()\t%&+@:')
        self.h = str.maketrans('ḫḪ', 'hH')
        self.g = str.maketrans('ĝĜ', 'ŋŊ')
        self.digits = str.maketrans(NUMERIC+X_NUMERIC, INDEX+X_INDEX)

    def subscribe_indices(self, string):
        """ Convert digit-based indices into subscripts """
        
        last = ''
        last_is_subscript = False
        newstring = ''
        for e, c in enumerate(string):
           
            if e == len(string)-1:
                next_ = ''
            else:
                next_ = string[e+1]

            if c.isdigit() and last.isalpha():
                c = c.translate(self.digits)
                last_is_subscript = True
            elif last_is_subscript and c.isdigit():
                c = c.translate(self.digits)
            elif c == X_NUMERIC and next_ == '(' and last.isalpha():
                c = c.translate(self.digits)
            else:
                last_is_subscript = False
                
            last = c
            newstring += c
            
        return newstring

                     
    def accent_to_index(self, string):
        """ Convert accents into subscript indices """
        xlit = ''
        index = ''
        ## TODO: Fix French comments, e.g. ($à la$) -> not a3.
        for c in string + ' ':
            if c in self.two:
                index = INDEX[2]
            if c in self.three:
                index = INDEX[3]
            if c in self.split:
                xlit += index + c
                index = ''
            else:
                xlit += self.deaccent.get(c, c)
        xlit = re.sub('(⌉|\]|>+|\||#)([₂₃])', r'\2\1', xlit)
        return xlit.rstrip()


    def unify_determinatives(self, string, lower=True):
        """ Lower/uppercase determinatives """
        norm = ''
        string = re.sub('(^|-|\.)([fmd])\.', r'\1{\2}', string)

        
        if '{' in string:
            upper = False
            i = 0
            last = ''
            for c in string:
                if c == '{':
                    upper = True
                if c+last == '{{':
                    # Ignore glosses
                    upper = False
                elif c == '+' and string[i-1] == '{':
                    upper = False
                elif c == '}':
                    upper = False
                elif c in ('m', 'd', 'f', '1', 'I', 'i')\
                     and string[i-1] == '{' and string[i+1] == '}':
                    upper = False
                    if c in ('1', 'I'):
                        c = 'm'
                if upper:
                    if lower:
                        c = c.lower()
                    else:
                        c = c.upper()
                norm += c
                last = c
                i += 1
            string = norm
        return string


    def normalize_h(self, string):
        norm = string.translate(self.h)
        return norm

    def normalize_g(self, string):
        norm = string.translate(self.g)
        return norm
    
    @lru_cache(maxsize=128)
    def normalize_all(self, string, id_=None, lower=True):
        """ Run all relevant normalizations for string """
        norm = self.normalize_h(string)
        norm = self.normalize_g(norm)
        chars = set(norm)
        if chars.intersection(self.numbers):
            norm = self.subscribe_indices(norm)
        if chars.intersection(self.accents):
            norm = self.accent_to_index(norm)
        if '{' in norm or '.' in norm:
            norm = self.unify_determinatives(norm, lower)
        _logger(string, norm, id_)
        return norm



IGNORE = ('%', '($', '$')

class BracketMover():

    def __init__(self, ignore=IGNORE):
        self.left = '[⸢'
        self.right = ']⸣'
        self.ignore = ignore
        
    @lru_cache(maxsize=256)
    def move_brackets(self, xlit, hash_notation=False):
        """ Move sign-internal brackets to the beginning
        or end of the sign as in modern Oracc transliteration. E.g.

        Input:  u[r-s]aŋ ⸢a-a⸣ {d}išk[ur a]r₂-zu in-ga-i-i
        Output: [ur-saŋ] a#-a# {d}[iškur ar₂]-zu in-ga-i-i

        :param xlit           input transliteration (line or word)
        :param hash_notation  use # to indicate half-brackets
        
        :type xlit            str
        :type hash_notation   bool

        """

        ## This implementation is slow due to multiple iterations

        def _move(sign):
            """ Transducer for moving brackets """
            l_brackets = ''
            r_brackets = ''

            if re.match('.*[\]⸣].*[\[⸢].*', sign):
                """ Deal with cases like l]uga[l and [l]uga[l] """
                return re.sub('(.*)[\]⸣](.*)[\[⸢](.*)', r'\1\2\3', sign)

            new_sign = ''
            for c in sign:
                if c in self.left:
                    l_brackets += c
                elif c in self.right:
                    r_brackets += c
                else:
                    new_sign += c

            return l_brackets + new_sign + r_brackets

        self.half_stack = []

        def _hashtag(sign):
            """ Transducer for replacing half-brackets with hashes;
            ignore non-alphanumeric signs, empty signs, comments
            and code switches """
            if not sign: 
                return sign

            if sign.startswith(self.ignore):
                return sign

            if re.match('^\W+$', sign):
                return sign
            

            pop = False
            new_sign = ''
            for c in sign:
                if c == '⸢':
                    self.half_stack.append(c)
                    c = ''
                if c == '⸣':
                    pop = True
                    c = ''
                else:
                    new_sign += c

            if self.half_stack:
                if pop:
                    self.half_stack.pop(0)
                return new_sign + '#'
        
            return new_sign

        """ Tokenize if input is a line """
        if ' ' in xlit:
            words = util.tokenize(xlit)
        else:
            words = [xlit]

        output = []
        for word in words:

            signs, delimiters = util.unzip_xlit(word)
            signs = [_move(s) for s in signs]

            if hash_notation:
                signs = [_hashtag(s) for s in signs]
                    
            output.append(util.zip_xlit(signs, delimiters))

        if self.half_stack:
            self.half_stack = []

        return ' '.join(output)


def unit_test():

    status = [0,0] 
    XT = Harmonizer()

    print('> Running unit test...')
    pairs = [('lu-lú-lùl-sa4', 'lu-lu₂-lul₃-sa₄', True),
             ('lu-lú-[lù]l-sa44', 'lu-lu₂-[lu]l₃-sa₄₄', True),
             ('lu-lú(|DUR6.Á|)-lùl#-sa14', 'lu-lu₂(|DUR₆.A₂|)-lul₃#-sa₁₄', True),
             ('lu-lú(|DÚR+Á|){KI}-lùl-sa4', 'lu-lu₂(|DUR₂+A₂|){ki}-lul₃-sa₄', True),
             ('lu-l[ú(|DÚR%%Á|)-lù]l-sa4', 'lu-l[u₂(|DUR₂%%A₂|)-lu]l₃-sa₄', True),
             ('lu111-lu2(|DUR2%%Á|)-lul3-sa4', 'lu₁₁₁-lu₂(|DUR₂%%A₂|)-lul₃-sa₄', True),
             ('lu#-lú(|DÚR×Á.U|)-{URÙDA}lùl-sa4', 'lu#-lu₂(|DUR₂×A₂.U|)-{uruda₃}lul₃-sa₄', True),
             ('lu-{[d]}lú(|DUR6×Á|)-lùl-sa4#', 'lu-{[d]}lu₂(|DUR₆×A₂|)-lul₃-sa₄#', True),
             ('<lú(|DU16%%DU3|)>-{t[ú]g}lùl{+lu-ul}', '<lu₂(|DU₁₆%%DU₃|)>-{t[u]g₂}lul₃{+lu-ul}', True),
             ('{D}30', '{d}30', True),
             ('60-x', '60-x', True),
             ('EN+60', 'EN+60', True),
             ('1/2', '1/2', True),
             ('14.KAM2', '14.KAM₂', True)
             ('6.4.0.1(DIŠ)', '6.4.0.1(DIŠ)', True),
             ('{M}da-da', '{M}da-da', False),
             ('{F}da-da', '{f}da-da', True),
             ('f.da-da', '{f}da-da', True),
             ('m.da-d.da', '{m}da-{d}da', True),
             ('f.am.mu.ud.da', '{f}am.mu.ud.da', True),
             ('f.am.mu.ud.d.da', '{f}am.mu.ud.{d}da', True),
             ('{1}da-da', '{m}da-da', True),
             ('{M}{d}da-da', '{m}{d}da-da', True),
             ('kirix(|DA.DU|)-{d}MÚ{+mu!(BÁ)}', 'kiriₓ(|DA.DU|)-{d}MU₂{+mu!(BA₂)}', True),
             ('{dug}kirix(|DA.DU|){KI}-{d}MÚ{+mu!(BÁ)}', '{DUG}kiriₓ(|DA.DU|){KI}-{d}MU₂{+mu!(BA₂)}', False)]
    
    for source, target, det in pairs:

        output = XT.unify_determinatives(source, lower=det)
        output = XT.subscribe_indices(output)
        output = XT.accent_to_index(output)

        if output == target:
            status[0] += 1
        else:
            status[1] += 1
            print(f'>fail: {source} \t {output} \t {target}')

    if not status[1]:
        print(f'> All {status[0]} tests passed')
    else:
        print(f'> {status[1]} tests failed out of {status[0]+status[1]}')

        
#unit_test()


xt = Harmonizer()
bm = BracketMover(IGNORE)

def digit_to_index(xlit):
    return xt.subscribe_indices(xlit)

def accent_to_index(xlit):
    return xt.accent_to_index(xlit)

def unify_determinatives(xlit, lower=True):
    return xt.unify_determinatives(xlit, lower)

def unify_h(xlit):
    return xt.normalize_h(xlit)

def unify_g(xlit):
    return xt.normalize_g(xlit)

def harmonize_all(xlit, lower_dets=True):
    return xt.normalize_all(xlit, id_=None, lower=lower_dets)
 
def move_brackets(xlit, hash_notation=False):
    return bm.move_brackets(xlit, hash_notation)
    

