#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import random
from collections import Counter
from operator import add
from postcorrect.korp_tags import map_to_korp
import postcorrect.xlit_tools

"""                                                 asahala 2020

Converts Korp VRT into CONLL-U for training the neural parser

"""

MAXLEN = 500
DIV = '-'*48
LANG_REGEX = re.compile('.*(Babylonian).*')

TEST = 0
DEV = 1

ERRORFILE = None
LOGFILE = None
XT = xlit_tools.XLITTools()
LT = xlit_tools.LemmaTools(ERRORFILE)

def unescape(pos):
    return pos.split(' ')[0].replace('&amp;', '&')

def normalize(string, id_=None):
    return XT.normalize_all(string, id_)

def is_valid(elems, genre):
    if not re.match(LANG_REGEX, elems['lang']):
        return
    #if genre not in ('legal transaction', 'administrative letter', 'administrative record'):
    #    return
    if '_' in elems['lem']:
        return
    if 'lexical' in genre:
       return
    if '*' in elems['xlit']:
        return
    return True

def process(filename):
    print('> Processing %s...' % filename)
    with open(filename, 'r', encoding='utf-8') as f:
        sentence = []
        for line in f.read().splitlines():
            if line.startswith('<text'):
                genre = re.sub('.* period="(.+?)".*', r'\1', line)
                cdli_id = re.sub('.*cdlinumber="(.+?)".*', r'\1', line)
                if "language" in genre:
                    print(line)
            if line.startswith('</sentence'):
                """ Build fake dependency trees """
                if sentence:
                    if len(sentence) > MAXLEN:
                        print('> Warning: Overlong sentence in %s!'\
                              % cdli_id)
                    tree = []
                    for i, word in enumerate(sentence, start=1):

                        """ Apply normalizations """
                        lemma = LT.fix_lemma(word['lem'], word['pos'])
                        lemma = XT.normalize_h(lemma)
                        xlit = XT.normalize_h(word['xlit'])
                        #lemma = normalize(lemma, 'lemma')
                        #xlit = normalize(word['xlit'], 'xlit')
                        xlit = XT.unify_determinatives(xlit)
                        #xlit = re.sub('([a-zṭš])[₁₂₃₄₅₆₇₈₉₀]', r'\1', xlit)
                        xcript = word['phon']

                        if lemma == 'X':
                            lemma = 'x'

                        tree.append('\t'.join([str(i),
                                      xlit,
                                      lemma, #xscript
                                      word['pos'],
                                      word['pos'], #tmp : korp_pos !
                                      'empty',
                                      {1:'0'}.get(i, '1'),
                                      {1:'root'}.get(i, 'child'),
                                      '_',
                                      word['eng']
                                      ]))
                    yield {'data': tree, 'genre': genre}
                sentence = []

            elif not line.startswith('<') and line:
                """ Gather word attributes from VRT """
                d = line.split('\t')

                """ Discard unlemmatized words """
                
                
                elems = {'xlit': d[0], 'lem': d[1], 'eng': d[2],
                         'phon': d[4],
                         'korp_pos': map_to_korp(d[5]),
                         'pos': unescape(d[6]), 'normname': d[7],
                         'lang': d[8], 'url': d[9]}

                """ Lemmatize integers left blank in Oracc (skip
                all other numbers) """
                #if elems['pos'] == 'n':
                #    if elems['xlit'].isdigit():
                #        elems['lem'] = elems['xlit']

                """ Prefer normalized names if available """
                if elems['normname'] != '_':
                    elems['lem'] = elems['normname']

                """ Validate attributes """
                if is_valid(elems, genre) is not None:
                    sentence.append(elems)
                    
                #sentence.append(re.sub(r"&(?![^\t\n]+;)", r"&amp;", line))

    """ Save change log """
    if LOGFILE is not None:
        xlit_tools.save_log(LOGFILE)

def save_data(trees, prefix):

    train = open(prefix + '-train.conllu', 'w', encoding='utf-8')
    dev = open(prefix + '-dev.conllu', 'w', encoding='utf-8')
    test = open(prefix + '-test.conllu', 'w', encoding='utf-8')

    genres = {}
    for i, tree in enumerate(trees):
        genres.setdefault(tree['genre'], [0,0,0])
        data = tree['data']
        word_count = len(data)
        if i % 10 == TEST:
            genres[tree['genre']][0] += word_count
            print('\n'.join(data) + '\n', file=test)
        elif i % 10 == DEV:
            genres[tree['genre']][1] += word_count
            print('\n'.join(data) + '\n', file=dev)
        else:
            genres[tree['genre']][2] += word_count
            print('\n'.join(data) + '\n', file=train)

    print('> Created files:\n * %s' % '\n * '.join([train.name, dev.name, test.name]))

    print('\n{:<25s} {:<5s} {:<5s} {:<5s}\n{}'\
          .format('GENRE', 'TEST', 'DEV', 'TRAIN', DIV))

    totals = [0, 0, 0]
    for k, v in sorted(genres.items(), key=lambda x: sum(x[1]), reverse=True):
        print('{:<25s} {:<5d} {:<5d} {:<5d}'.format(k, *v))
        totals = list(map(add, totals, v))
    print(DIV)
    print('{:<25s} {:<5d} {:<5d} {:<5d}'.format('TOTAL', *totals))
    
    train.close()
    dev.close()
    test.close()


if __name__ == '__main__':
    trees = process('../data/ORACC19.VRT')
    save_data(trees)
