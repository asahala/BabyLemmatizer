#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from cuneiformtools import util, norm, alphabet
from cuneiformtools import tests
from functools import lru_cache
from preferences import Tokenizer

""" BabyLemmatizer 2 preprocessor 

asahala 2023

"""

LACUNA_METACHARS = frozenset(alphabet.LACUNA_META)

@lru_cache(maxsize=256)
def lowercase_determinatives(xlit):
    return norm.unify_determinatives(xlit, lower=True)


@lru_cache(maxsize=256)
def uppercase_determinatives(xlit):
    return norm.unify_determinatives(xlit, lower=False)


@lru_cache(maxsize=512)
def subscribe_indices(xlit):
    xlit = norm.digit_to_index(xlit)
    xlit = norm.accent_to_index(xlit)
    return xlit


def unify_h(xlit):
    return norm.unify_h(xlit)


def remove_brackets(xlit):
    return ''.join(c for c in xlit if c not in LACUNA_METACHARS)
    
    
@lru_cache(maxsize=256)
def reformat(sign):
    """ Reformat cuneiform input """
    sign = sign.replace('*', '') # remove stars
    
    if sign.upper() == sign:
        return sign
    elif sign.lower() == sign:
        """ Remove indices only if tokenizer setting 0 is used """
        if Tokenizer.setting == 1:
            return ' '.join(c for c in sign)
        return ' '.join(c for c in sign if not c.isdigit())
    else:
        return sign

@lru_cache(maxsize=512)
def get_chars_lemma(lemma):
    return ' '.join(list(lemma))


@lru_cache(maxsize=512)
def get_chars(xlit):

    """ It seems that the best tokenization for Akkadian includes
    
    - logo-syllabic tokenization
    - removal of indices for lowerase
    - preserving indices for uppercase
    - splitting logograms at .
    
    """
    
    if xlit == '_':
        return xlit

    """ If used for languages with alphabet """
    if Tokenizer.setting == 2:
        return ' '.join(list(xlit))

    #return ' '.join(list(xlit))
    ## TODO MAKE THESE OPTIONAL
    xlit = xlit.replace('*', '')
    xlit = xlit.replace('{d}+', '{d}')

    xlit = uppercase_determinatives(xlit)
    signs, delimiters = util.unzip_xlit(xlit)
    delimiters = [f' {d} '.replace('{ ', '{').replace(' }', '}') for d in delimiters]
    signs = [reformat(s) for s in signs]
    
    xlit_ = util.zip_xlit(signs, delimiters)\
            .lstrip()\
            .rstrip()
    xlit_ = re.sub('(\{\+)(.+?)(\})', r'\1 \2 \3', xlit_)
    xlit_ = re.sub(' +', ' ', xlit_)
    #xlit_ = re.sub(' ?- ?', ' ', xlit_) ## TMP remove dashes
    #xlit_ = xlit_.replace(' . ', '.') ### TEMP
    return xlit_    
 

@lru_cache(maxsize=512)
def get_signs(xlit):
    return ' '.join(
        (sign for sign in util.unzip_xlit(xlit)[0] if sign))


#@lru_cache(maxsize=1024)
#def to_tagger_input(stack):
#    tokens = [x[0] for x in stack]
#    return '{} << {} >> {}\n'.format(*tokens)


#@lru_cache(maxsize=1024)
#def to_lemmatizer_input(stack):
#    token = stack[1][0]
#    context = f'PREV={stack[0][2]} UPOS={stack[1][2]} NEXT={stack[2][2]}'
#    return f'{token} {context}\n'


@lru_cache(maxsize=1024)
def clean_traindata(xlit):
    xlit = remove_brackets(xlit)
    xlit = uppercase_determinatives(xlit)
    #xlit = xlit.replace('{d}+', '{d}')
    xlit = get_chars(xlit)
    return xlit


def make_tagger_src(formctx, context):
    """ Format FORM context for training data """
    return ' | '.join(f'<< {get_chars(xlit)} >>'
            if e == context else f'{get_chars(xlit)}'
                      for e, xlit in enumerate(formctx.split('|')))

def make_lem_src(form, xposctx):
    """ Format XPOS context for training data """
    xlit = get_chars(form)
    xpos = ' '.join(f'P{e}={pos}' for e, pos in enumerate(xposctx.split('|')))
    return f'{xlit} {xpos}'


