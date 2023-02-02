#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import math
from collections import defaultdict
from preferences import python_path, onmt_path
import preprocessing
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

        for stack in conllutools.get_training_data2(filename):
            if stack is None:
                continue
            
            if stack == conllutools.EOU:
                pos_src.write('<EOU>\n')
                pos_tgt.write('<EOU>\n')
                lem_src.write('<EOU>\n')
                lem_tgt.write('<EOU>\n')
                continue
            
            pos_src.write(preprocessing.to_tagger_input(stack))
            pos_tgt.write(stack[1][2] + '\n')
            lem_src.write(preprocessing.to_lemmatizer_input(stack))
            lem_tgt.write(stack[1][1] + '\n')
            statistics[filename] += 1

    
    """ Build YAML-definitions for models. The network architecture
    and its parameters follow (Kanerva, Ginter & Salakoski 2020),
    i.e. TurkuNLP's Universal Lemmatizer where BabyLemmatizer 1.0 was
    based on. """

    if data_type == 'train':
        
        examples = statistics[filename]
        steps_per_epoch = int(math.ceil(int(examples) / 64))
        total_steps = int(examples * 0.15)
        start_decay = int(math.ceil(total_steps /2))

        hyper = base_yaml.set_hyper(examples, steps_per_epoch, total_steps, start_decay)
        base_yaml.make_lemmatizer_yaml(prefix, f'./models/{prefix}/', hyper)
        base_yaml.make_tagger_yaml(prefix, f'./models/{prefix}/', hyper)
                        

            
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

    for model in model_names:
        model_path = f'./models/{model}/'
        for yaml in (x for x in os.listdir(model_path) if x.endswith('.yaml')):
            os.system(f'{python_path}python {onmt_path}build_vocab.py '\
                      f'-config {model_path}{yaml} -n_sample -1 -num_threads 2')
            os.system(f'{python_path}python {onmt_path}train.py '\
                      f'-config {model_path}{yaml}')    
    
build_train_data()
train_models('lbtest1', 'lbtest2', 'lbtest3', 'lbtest4', 'lbtest5')
#train_models('lbtest1')
