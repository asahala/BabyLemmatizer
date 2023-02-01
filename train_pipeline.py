#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from functools import lru_cache
from collections import defaultdict
from cuneiformtools import util
import conllutools
import base_yaml

""" ===========================================================
Training data builder and trainer for BabyLemmatizer 2

asahala 2023
https://github.com/asahala

University of Helsinki
   Origins of Emesal Project
   Centre of Excellence for Ancient Near-Eastern Empires

=========================================================== """

statistics = defaultdict(int)

@lru_cache(maxsize=512)
def get_signs(xlit):
   
    return ' '.join(
        (sign for sign in util.unzip_xlit(xlit)[0] if sign)
        )


def reformat(sign):

    if sign.upper() == sign:
        return sign
    elif sign.lower() == sign:
        return ' '.join(c for c in sign if not c.isdigit())
    else:
        return sign


def get_chars(xlit):

    signs, delimiters = util.unzip_xlit(xlit)

    delimiters = [f' {d} '.replace('{ ', '{').replace(' }', '}') for d in delimiters]
    signs = [reformat(s) for s in signs]

    #print(xlit, signs)

    xlit_ = util.zip_xlit(signs, delimiters).lstrip().rstrip().replace('  ', ' ').replace('  ', ' ').replace('{+ ', '{+')

        
    return xlit_
    #return ' '.join(list(xlit))


def print_statistics():
    print('> Training data item counts:')
    for k, v in statistics.items():
        print('', v, k, sep='\t')

def make_training_data(filename):
    """ Build training data for POS-tagger and lemmatizer.
    The data is saved to `TRAIN_PATH`. Source files must be
    in CONLL-U format and named PREFIX-SUFFIX.conllu, where
    prefix is arbitrary identifier and suffix `dev`, `test`,
    or `train` depending on which set the data belongs. """

    print(f'> Building training data from {filename}')

    """ Create required folder structures for the model """
    o_fn = filename.split('/')[-1]
    prefix = o_fn.split('-')[0]
    data_type = o_fn.split('-')[-1].replace('.conllu', '')
    paths = ('./models/',
        f'./models/{prefix}/',
        f'./models/{prefix}/tagger/',
        f'./models/{prefix}/lemmatizer/',
        f'./models/{prefix}/tagger/traindata/',
        f'./models/{prefix}/lemmatizer/traindata/',
        f'./models/{prefix}/eval/')

    for path in paths:
        try:
            os.mkdir(path)
        except FileExistsError:
            pass

    """ Build YAML-definitions for models """
    base_yaml.make_lemmatizer_yaml(prefix, f'./models/{prefix}/')
    base_yaml.make_tagger_yaml(prefix, f'./models/{prefix}/')

    """ Generate training data """
    tagger_path = f'./models/{prefix}/tagger/traindata/'
    lemmatizer_path = f'./models/{prefix}/lemmatizer/traindata/'

    pos_src_fn = f'{tagger_path}{data_type}.src'
    pos_tgt_fn = f'{tagger_path}{data_type}.tgt'
    lem_src_fn = f'{lemmatizer_path}{data_type}.src'
    lem_tgt_fn = f'{lemmatizer_path}{data_type}.tgt'

    with open(pos_src_fn, 'w', encoding='utf-8') as pos_src,\
         open(pos_tgt_fn, 'w', encoding='utf-8') as pos_tgt,\
         open(lem_src_fn, 'w', encoding='utf-8') as lem_src,\
         open(lem_tgt_fn, 'w', encoding='utf-8') as lem_tgt:

        """ Build a stack of size 3 from words in the corpus to take
        adjacent words into account; each item in the stack consists of
        tuple (FORM, LEMMA, UPOS). Sources are split into signs. """
        
        stack = []
        for word in conllutools.get_training_data(filename):
            stack.append(word)
            if len(stack) == 3:
                if stack[1] != conllutools.EOU:
                    signs = [get_signs(x[0]) for x in stack]
                    tokens = [get_chars(x[0]) for x in stack]
                    pos_src.write('{} << {} >> {}\n'.format(*tokens))
                    pos_tgt.write(stack[1][2] + '\n')
                    lem_src.write(f'{tokens[1]} PREV={stack[0][2]} UPOS={stack[1][2]} NEXT={stack[2][2]}\n')
                    lem_tgt.write(f'{stack[1][1]}\n')
                stack.pop(0)
            statistics[filename] += 1


def build_train_data(conllu_path='./conllu/'):
    """ Run this method to rebuild training data based on Conllu-file """
    filelist = (x for x in os.listdir(conllu_path) if x.endswith('.conllu'))
    for filename in filelist:
        make_training_data(conllu_path + filename)
    print_statistics()


def train_models(*model_names):
    """ Run this method to train the models; this simply calls OpenNMT
    from the command line with required parameters to train basic
    models for raw tagging and lemmatization.

    :param model_names           model names that correspond to
                                 prefixes in your conllu files
    :type model_names            str """

    python_path = '/projappl/clarin/onmt/OpenNMT/bin/'
    onmt_path = './OpenNMT-py/onmt/bin/'

    for model in model_names:
        model_path = f'./models/{model}/'
        for yaml in (x for x in os.listdir(model_path) if x.endswith('.yaml')):
            os.system(f'{python_path}python {onmt_path}build_vocab.py -config {model_path}{yaml} -n_sample -1 -num_threads 2')
            os.system(f'{python_path}python {onmt_path}train.py -config {model_path}{yaml}')    
    
build_train_data()
train_models('lbtest1', 'lbtest2', 'lbtest3', 'lbtest4', 'lbtest5')
