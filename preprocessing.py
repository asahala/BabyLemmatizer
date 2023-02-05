#!/usr/bin/python
# -*- coding: utf-8 -*-

from cuneiformtools import util, norm, alphabet
from functools import lru_cache

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
    if sign.upper() == sign:
        return sign
    elif sign.lower() == sign:
        return ' '.join(c for c in sign if not c.isdigit())
    else:
        return sign


@lru_cache(maxsize=512)
def get_chars(xlit):
    if xlit == '_':
        return xlit
    signs, delimiters = util.unzip_xlit(xlit)
    delimiters = [f' {d} '.replace('{ ', '{').replace(' }', '}') for d in delimiters]
    signs = [reformat(s) for s in signs]
    xlit_ = util.zip_xlit(signs, delimiters).lstrip().rstrip().replace('  ', ' ').replace('  ', ' ').replace('{+ ', '{+')       
    return xlit_    
 

@lru_cache(maxsize=512)
def get_signs(xlit):
    return ' '.join(
        (sign for sign in util.unzip_xlit(xlit)[0] if sign))


@lru_cache(maxsize=1024)
def to_tagger_input(stack):
    tokens = [x[0] for x in stack]
    return '{} << {} >> {}\n'.format(*tokens)


@lru_cache(maxsize=1024)
def to_lemmatizer_input(stack):
    token = stack[1][0]
    context = f'PREV={stack[0][2]} UPOS={stack[1][2]} NEXT={stack[2][2]}'
    return f'{token} {context}\n'


@lru_cache(maxsize=1024)
def clean_traindata(xlit):
    xlit = remove_brackets(xlit)
    xlit = uppercase_determinatives(xlit)
    xlit = get_chars(xlit)
    return xlit
