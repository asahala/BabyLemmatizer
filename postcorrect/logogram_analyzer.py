#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

""" Logogram analyzer                   asahala 2021-04

This script finds words that have the lowest confidence
score in lemmatization, i.e. logogram "roots" that the
neural net never saw in training.

On Babylonian data the accuracy rate for 0.0 confidence
scored lemmas is around 0.33, and on Non-Assyrian data
around 0.40. Thus all 0.0 scored words should be verified
manually.

Logogram is considered to be next-to-impossible to lemmatize if

   (1) it is not found in the training data with
       all syllabic suffixes and logographic morpheme markers
       stripped out
   (2) stripped logogram exists in training data, but only
       with a different determinative.

"""

""" Regex definitions for syllabic parts of logosyllabic spellings """
sign = r'[a-zʾšṣṭ₁₂₃₄₅₆₇₈₉₀]+?'
determinative = r'(\{[A-ZŠa-zʾšṣṭ₁₂₃₄₅₆₇₈₉₀]+?\})'
prefixes = r'^(%s-)+?' % sign
suffixes = r'((\.|-)MEŠ|\.HI\.A)?(-%s?%s)+?$' % (determinative, sign)
affixes = re.compile(prefixes + '|' + suffixes)

def deaffixate(string):
    """ Return stripped logogram """
    return re.sub(affixes, '', string)

def is_logogram(string):
    """ Check if input is a logogram """
    return not re.sub('\{.+?\}', '', string).islower()

def get_logograms(data):
    """ Extract all logograms from texts without any affixes

    :param data             parsed training conll-u file
    :type data              list """

    logograms = set()    
    for line in data:
        fields = line.split('\t')
        if len(fields) > 1:
            xlit = fields[1]
            if is_logogram(xlit):
                logograms.add(deaffixate(xlit))
    return logograms
                
def mark_oov_logograms(data, logogram_dict):
    """ Check if stripped logogram is found in ´logogram_dict´

    :param data             parsed test conll-u file
    :param logogram_dict    output of get_logograms()
    
    :type data              list
    :type logogram_dict     set """
    
    for line in data:
        fields = line.split('\t')
        if len(fields) > 1:
            xlit = fields[1]
            if is_logogram(xlit):
                if deaffixate(xlit) not in logogram_dict:
                    if fields[-1][0].isdigit():
                        # Only replace scores, not named items such as lac, num
                        fields[-1] = '0.0'
            yield '\t'.join(fields)
        else:
            yield ''
