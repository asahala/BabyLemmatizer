#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import math
import shutil
import re
from collections import defaultdict
from preferences import python_path, onmt_path, conllu_path
from command_parser import parse_prefix, split_train_filename
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


hr = '=' * 20
print(f'{hr} BabyLemmatizer 2.0 {hr}')

statistics = defaultdict(int)
counts = defaultdict(dict)
log = []

def logger(message):
    print(message)
    log.append(message)
    

def save_log(log_file):
    with open(log_file, 'w', encoding='utf-8') as f:
        for line in log:
            f.write(line + '\n')
    print(f'\n> Log saved to {log_file}')


def print_statistics():
    logger('> Training data item counts:')
    for k, v in statistics.items():
        logger(f'   {v}\t{k}')


def _rename_model(model_name, type_):
    
    def get_step(filename):
        return (''.join(c for c in filename if c.isdigit()))
        
    path = os.path.join('models', model_name, type_)
    step = sorted(get_step(x) for x in os.listdir(path)
                  if x.endswith('.pt') and x != 'model.pt')[-1]
    
    old_name = f'model_step_{int(step)}.pt'
    new_name = 'model.pt'
    os.rename(os.path.join(path, old_name), os.path.join(path, new_name))
    print(f'> Model {old_name} --> {new_name}')

    
def print_oov_rates():
    ## TODO: Rewrite this crap
    ## just do it in a single file
    for model in counts:
        stats = {}
        for data_type in ('dev', 'test'):
            for word_type in ('xlit', 'lem'):
                key = f'types-{data_type}-{word_type}'

                """ Get training and other data type counts """
                train = set(counts[model]['train'][word_type])
                this = set(counts[model][data_type][word_type])

                """ Make OOV dictionary and save it """
                out_of_vocab = this - train

                fn = f'models/{model}/override/'\
                     f'{data_type}-types-oov.{word_type}'
                
                with open(fn, 'w', encoding='utf-8') as f:
                    for w in sorted(out_of_vocab):
                        freq = counts[model][data_type][word_type][w]
                        f.write(f'{w}\t{freq}\n')

                """ Count absolute and relative freqs for types """
                examples_this = len(this)
                oov_abs = len(out_of_vocab)
                oov_rel = round(100 * oov_abs / examples_this, 2)
                stats[key] = (examples_this, oov_abs, oov_rel)

                """ Count absolute and relative freqs for tokens """                
                key = f'tokens-{data_type}-{word_type}'
                train = sum(counts[model]['train'][word_type].values())
                this = sum(counts[model][data_type][word_type].values())
                examples_this = this

                oov_abs = sum(counts[model][data_type][word_type][w]
                               for w in out_of_vocab)

                oov_rel = round(100 * oov_abs / examples_this, 2)
                stats[key] = (examples_this, oov_abs, oov_rel)

        headings = ('CATEGORY', 'SIZE', 'OOV', 'OOV-%')
        logger('\n   ' + model + ' ' + '='*48)
        logger('   {: <20} {:>7} {:>7} {:>7}'.format(*headings))
        for key, values in sorted(stats.items()):
            logger('   {: <20} {:>7} {:>7} {:>7}'.format(key, *values))           
           

def make_override(prefix, data_type, filename):
    """ Setup override """
    
    fn = f'models/{prefix}/override/{data_type}.all'
    fnl = f'models/{prefix}/override/{data_type}-types.lem'
    fnx = f'models/{prefix}/override/{data_type}-types.xlit'
    lemma_dict = defaultdict(int)
    xlit_dict = defaultdict(int)

    logger('   + Building override lexicons')
    with open(fn, 'w', encoding='utf-8') as f:
        for line in conllutools.get_override(filename):
            if line:
                f.write('\t'.join(line) + '\n')
                xlit, lemma, pos = line
                if xlit != conllutools.EOU[0]:
                    lemma_dict[f'{lemma} {pos}'] += 1
                    xlit_dict[xlit] += 1

    with open(fnl, 'w', encoding='utf-8') as fl:
        for word, freq in sorted(lemma_dict.items(),
                                 key=lambda item: item[1], reverse=True):
            fl.write(f'{word}\t{freq}\n')
            
    with open(fnx, 'w', encoding='utf-8') as fl:
        for word, freq in sorted(xlit_dict.items(),
                                 key=lambda item: item[1], reverse=True):
            fl.write(f'{word}\t{freq}\n')

    logger(f'   + {len(xlit_dict)} form types')
    logger(f'   + {len(lemma_dict)} lemma types')

    stats = {'lem': lemma_dict, 'xlit': xlit_dict}

    if not prefix in counts:
        counts[prefix] = {data_type: stats}
    else:
        counts[prefix][data_type] = stats


def _make_training_data(filename):
    """ Build training data for POS-tagger and lemmatizer.
    The data is saved to `TRAIN_PATH`. Source files must be
    in CONLL-U format and named PREFIX-SUFFIX.conllu, where
    prefix is arbitrary identifier and suffix `dev`, `test`,
    or `train` depending on which set the data belongs. """

    """ Create required folder structures for the model """
    orig_fn = os.path.split(filename)[-1]
    prefix, data_type = split_train_filename(orig_fn)
    
    logger(f'\n> Building training data from {filename}')

    ## TODO: define somewhere else globally
    ## or this will get really confusing at some point
    """ Define model path structure """
    paths = (
        'models',
        os.path.join('models', prefix),
        os.path.join('models', prefix, 'tagger'),
        os.path.join('models', prefix, 'lemmatizer'),
        os.path.join('models', prefix, 'tagger', 'traindata'),
        os.path.join('models', prefix, 'lemmatizer', 'traindata'),
        os.path.join('models', prefix, 'eval'),
        os.path.join('models', prefix, 'override'),
        os.path.join('models', prefix, 'conllu'))

    for path in paths:
        try:
            os.mkdir(path)
        except FileExistsError:
            pass

    """ Save CoNLL-U to model for reproducibility """
    shutil.copyfile(
        filename,
        os.path.join('models', prefix, 'conllu', f'{data_type}.conllu'))    

    """ Generate training data """
    tagger_path = os.path.join(
        'models', prefix, 'tagger', 'traindata')
    lemmatizer_path = os.path.join(
        'models', prefix, 'lemmatizer', 'traindata')

    """ Define target and source files for NN-training data """
    pos_src_fn = os.path.join(tagger_path, f'{data_type}.src')
    pos_tgt_fn = os.path.join(tagger_path, f'{data_type}.tgt')
    lem_src_fn = os.path.join(lemmatizer_path, f'{data_type}.src')
    lem_tgt_fn = os.path.join(lemmatizer_path, f'{data_type}.tgt')

    logger('   + Building tagger and lemmatizer training sets')

    EOU = conllutools.EOU[0]
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

            if stack == EOU:
                pos_src.write(f'{EOU}\n')
                pos_tgt.write(f'{EOU}\n')
                lem_src.write(f'{EOU}\n')
                lem_tgt.write(f'{EOU}\n')
                continue

            """ Define source and target format for train data """
            pos_src.write(preprocessing.to_tagger_input(stack))
            pos_tgt.write(stack[1][2] + '\n')
            lem_src.write(preprocessing.to_lemmatizer_input(stack))
            lem_tgt.write(' '.join(list(stack[1][1])) + '\n')
            statistics[filename] += 1

    
    """ Build YAML-definitions for models. The network architecture
    and its parameters follow (Kanerva, Ginter & Salakoski 2020),
    i.e. TurkuNLP's Universal Lemmatizer where BabyLemmatizer 1.0 was
    based on. Also build override lexicons for future use. """

    if data_type == 'train':

        """ Setup neural net """
        examples = statistics[filename]
        steps_per_epoch = int(math.ceil(int(examples) / 64))
        total_steps = int(examples * 0.15)
        start_decay = int(math.ceil(total_steps /2))

        hyper = base_yaml.set_hyper(
            examples,
            steps_per_epoch,
            total_steps,
            start_decay)

        base_yaml.make_lemmatizer_yaml(
            prefix,
            os.path.join('models', prefix),
            hyper)

        base_yaml.make_tagger_yaml(
            prefix,
            os.path.join('models', prefix),
            hyper)

    make_override(prefix, data_type, filename)


def build_train_data(*models, conllu_path=conllu_path):
    """ Build train data from CoNLL-U files in the given
    folder.

    :param models         arbitrary number of model names that
                          correspond to file prefixes in the conllu path
    :param conllu_path    location of CoNLL-U files

    :type models          str
    :type models          str                        """
    
    filelist = [x for x in os.listdir(conllu_path)
                if x.endswith('.conllu') and x.startswith(tuple(models))]

    if not filelist:
        print(f'\n> Path "{conllu_path}" does not contain'\
              ' files with given prefix')
        sys.exit(0)
    
    for filename in sorted(filelist):
        _make_training_data(os.path.join(conllu_path, filename))
        
    print_statistics()
    print_oov_rates()

    """ Get model prefix by removing digits """
    if len(models) > 1:
        prefix = ''.join(c for c in models[0] if not c.isdigit())
    else:
        prefix = models[0]
        
    save_log(f'build-log-{prefix}.txt')


def train_model(*models, cpu=False):
    """ Run this method to train the models; this simply calls OpenNMT
    from the command line with required parameters to train basic
    models for raw tagging and lemmatization.

    :param models         arbitrary number of model names that
                          correspond to file prefixes in the conllu path

    :type models          str """

    if cpu:
        gpu = ''
    else:
        gpu = '-gpu_ranks 0 -world_size 1'

    for model in sorted(models):
        if model not in os.listdir('models'):
            print(f'> Run build_training_data({model}) before training.')
            sys.exit(0)

        model_path = os.path.join('models', model)
        for yaml in (x for x in os.listdir(model_path) if x.endswith('.yaml')):
            os.system(f'{python_path}python {onmt_path}build_vocab.py '\
                      f'-config {model_path}/{yaml} -n_sample -1 '\
                      f'-num_threads 2')
            os.system(f'{python_path}python {onmt_path}train.py '\
                      f'-config {model_path}/{yaml} {gpu}')

        _rename_model(model, 'lemmatizer')
        _rename_model(model, 'tagger')


if __name__ == "__main__":
    prefix = 'urartian0'
    models = parse_prefix(prefix)
    build_train_data(*models)
    #train_model('a', 'b')#*models)
    pass

