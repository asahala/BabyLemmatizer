#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Python implementation for OGSL """

import re
import cuneiformtools.io as io
import cuneiformtools.util as util
import cuneiformtools.norm as norm
import cuneiformtools.aa_data as anderson
from cuneiformtools.alphabet import CONSONANT, VOWEL, DELIMITERS, REMOVE_INDEX
from cuneiformtools.ogsl_data import sign_list
from functools import lru_cache


_lookup = {}
_lookup_r = {}

for key in sign_list['signs']:
    values = sign_list['signs'][key].get('values', None)
    if values is not None:
        _lookup.setdefault(key, values)
        for v in values:
            _lookup_r[v] = key


def _remove_indices(string):
    return string.translate(REMOVE_INDEX).replace('_', '')

def credits():
    print('Oracc Global Sign List')
    print(io.DIV)
    for key in ('project', 'source', 'license', 'license-url',
                'more-info', 'UTC-timestamp'):
        print(f'{io.INDENT}{key}: {sign_list[key]}')
    print('\n')
    print('Original AA-Sign list spreadsheet')
    print(io.DIV)
    print(f'{io.INDENT}author: {anderson.credits}')

def version():
    print(f"OGSL version: {sign_list['UTC-timestamp']}")
    print(f"AA-Sign list version: {anderson.version}")


def _sort(array, sort_index=0, sort=True):
    if sort:
        return util.sort(array, sort_index)
    else:
        return array


def _set_sort_key(sort_index):
    return sort_index != 'reading'


def _collect_phonemic(phonemic, normalize):
    for key, values in _lookup.items():
        for value in values:
            if re.match('^%s$' % phonemic, _remove_indices(value)):
                yield (value, key)

       
def get_name(reading, normalize=False):
    """ Return name of the cuneiform sign

    :param reading      reading of sign
    :type reading       str

    """
    reading = norm.harmonize_all(reading)
    
    for name, readings in _lookup.items():
        if reading in readings:
            return name


def get_readings(sign, sort=False, normalize=False):
    """ Return name of the cuneiform sign

    :param sign       name or reading of sign
    :param sort       sort the results before returing
    
    :type sign        str
    :type sort        bool
    
    """
    sign = norm.harmonize_all(sign)

    if sign.islower():
        sign = get_name(sign)
    readings = _lookup.get(sign, None)

    if readings is not None:
        return _sort(readings, sort_index=0, sort=sort)
    print(f'Sign {sign} not in OGSL.')
    return


def get_homophones(reading, sort_by='reading', sort=False, normalize=False):
    """ Return homophones for reading

    :param reading       reading that homophones are searched for
    :param sort_by       sort results by `name` (0) or `reading` (1)
    :param sort          sort the results befor returning
    
    :type sign           str
    :type sort_by        int or str
    :type sort           bool
    
    """
    if normalize:
        reading = norm.harmonize_all(reading)


    
    sort_by = _set_sort_key(sort_by)
    phonemic = _remove_indices(reading)
    found = list(_collect_phonemic(phonemic, normalize))
    return _sort(found, sort_by, sort)     


def get_abstract(pattern, sort_by='reading', sort=False):
    """ Get all signs that have a given phonemic pattern,
    for example *C:Vr* will match all readings that contain
    at least one geminate followed by any vowel and /r/, e.g
    lammar, dimmer, saggar, babbar...

    :param pattern       search pattern using wild cards:
                           V for vowel
                           C for consonant
                           : for phonemic length
                           . for any single phoneme
                           * for zero or more anything
                           
    :param sort_by       sort results by `name` (0) or `reading` (1)
    :param sort          sort the results before returning
    
    :type pattern        str
    :type sort_by        int or str
    :type sort           bool

    """

    sort_by = _set_sort_key(sort_by)
    
    chars = {'V': '([%s])' % VOWEL,
             'C': '([%s])' % CONSONANT,
             ':': r'\_',
             '.': '([%s%s])' % (CONSONANT, VOWEL),
             '*': '([%s%s-])*' % (CONSONANT, VOWEL)}
    regex = ''
    
    """ Set regex back-references """
    group = 0
    found = []
    for c in ''.join([chars.get(c, c) for c in pattern]):
        if c == ')':
            group += 1
        elif c == '_':
            c = str(group)
        regex += c
    found = list(_collect_phonemic(regex))
    
    return _sort(found, sort_by, sort)


def contains_sign(sign, position='', sort=False, normalize=False):
    ## Todo: deal with medial positions
    """ Return signs that contain given sign, for example,
    ´AN´ with ´final´ would return |A.AN|, |KU.AN| etc.

    :param sign         sign to search for
    :param position     position within the targets:
                        ´initial´, ´final´, ´middle´
    :param sort         sort the results before returning

    :type sign          str
    :type position      str
    :type sort          bool
    
    """

    if normalize:
        sign = norm.harmonize_all(sign)
    
    initial = '|' + sign + '.' 
    middle = '.' + sign + '.'
    final = '.' + sign + '|'
    
    if position == 'initial':        
        array = [sign for sign in _lookup
                 if sign.startswith(initial)]
    elif position == 'final':
        array = [sign for sign in _lookup
                 if sign.endswith(final)]
    elif position == 'middle':
        array = [sign for sign in _lookup
                 if (middle) in sign]
    else:
        array = [sign for sign in _lookup
                 if (initial) in sign
                 or (middle) in sign
                 or (final) in sign]
        
    return _sort(array, 0, sort)


def get_number(sign, normalize=False):
    ## TODO: Deal with compound signs
    """ Return sign's number in Labat, OBO and Borger

    :param sign         sign to search number for
    :param source       source for the number, options:
                        `Labat`, `Borger`, `OBO`

    :type sign          str
    :type source        str

    """
    if normalize:
        sign = norm.harmonize_all(sign)

    if sign.islower():
        sign = get_name(sign)

    return anderson.sign_list.get(sign, None)


@lru_cache(maxsize=128)
def _map_signs(xlit):
    """ Helper for sign-level tokenization """

    def _split(s):
        """ Iterate input character by character and
        yield sign at delimiters. Spare x-indices
        as sign names and spare piped compound signs
        e.g. kurₓ(DU) -> DU, |UD.DU| -> |UD.DU| """

        sign = ''
        pipe = ''
        for c in s:
            if c in DELIMITERS:
                if not pipe:
                    yield sign
                    sign = ''
                else:
                    sign += c
            elif c in '+)':
                pass
            elif c == '(':
                sign = ''
            elif c == '|':
                sign += c
                if not pipe:
                    pipe += c
                else:
                    pipe = ''
            else:
                if pipe:
                    sign += c.upper()
                else:
                    sign += c.lower()
        yield sign

    return [_lookup_r.get(s, s) for s in _split(xlit) if s]

    
def get_signs(xlit, ignore_glosses=False, normalize=False):
    """ Return sign names for every sign in a transliterated word.

    :param xlit            transliterated word
    :type xlit             str

    """
    if normalize:
        xlit = norm.harmonize_all(xlit, lower_dets=True)

    if ignore_glosses:
        xlit = re.sub('({\+.+?})', '', xlit)
    
    return _map_signs(xlit)


def compare_xlit(xlit1, xlit2, ignore_glosses=False, normalize=False):
    """ Compare two transliterations on sign level. Useful for
    finding matches between different transliteration conventions,
    e.g. a-ka₃-am-gim == a-ga-am-gin₇.

    :param xlit1           transliterated word1
    :param xlit2           transliterated word1
    
    :type xlit1            str
    :type xlit2            str
    
    """
    
    return get_signs(xlit1, ignore_glosses, normalize) ==\
           get_signs(xlit2, ignore_glosses, normalize)
        
        
#def get_values(self, name, sort=False):
#    """ Return values by sign name """
#    if name.islower():
#        name = self.get_name(name)
#    values = self.list.get(name, None)
#    return self.sort(values, 0, sort)
