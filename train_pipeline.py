#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import math
import shutil
import re
from collections import defaultdict
from preferences import python_path, onmt_path, Paths
from command_parser import parse_prefix, split_train_filename
import preprocessing as PP
import conllutools
import conlluplus
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
        
    path = os.path.join(Paths.models, model_name, type_)
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

                fn = os.path.join(Paths.models, model, 'lex',
                     f'{data_type}-types-oov.{word_type}')
                
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
           

def make_lexicon(prefix, data_type, filename):
    """ Setup lexicon """
    ### TODO: rewrite this, uses still old conllu module
    fn = os.path.join(
        Paths.models, prefix, 'lex', f'{data_type}.all')
    fnl = os.path.join(
        Paths.models, prefix, 'lex', f'{data_type}-types.lem')
    fnx = os.path.join(
        Paths.models, prefix, 'lex', f'{data_type}-types.xlit')
    lemma_dict = defaultdict(int)
    xlit_dict = defaultdict(int)

    logger('   + Building lexicons')
    with open(fn, 'w', encoding='utf-8') as f:
        for line in conllutools.get_lexicon(filename):
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

    context = 1
    
    """ Create required folder structures for the model """
    orig_fn = os.path.split(filename)[-1]
    prefix, data_type = split_train_filename(orig_fn)
    
    logger(f'\n> Building training data from {filename}')

    """ Define model path structure """
    ## TODO: makedirs
    paths = (
        Paths.models,
        os.path.join(Paths.models, prefix),
        os.path.join(Paths.models, prefix, 'override'),
        os.path.join(Paths.models, prefix, 'tagger'),
        os.path.join(Paths.models, prefix, 'lemmatizer'),
        os.path.join(Paths.models, prefix, 'tagger', 'traindata'),
        os.path.join(Paths.models, prefix, 'lemmatizer', 'traindata'),
        os.path.join(Paths.models, prefix, 'eval'),
        os.path.join(Paths.models, prefix, 'lex'),
        os.path.join(Paths.models, prefix, 'conllu'))

    for path in paths:
        try:
            os.mkdir(path)
        except FileExistsError:
            pass

    """ Load CoNLL-U+ file """
    this_data = conlluplus.ConlluPlus(filename)
    this_data.normalize(is_traindata=True)
    """ Fill in context information and save file to model dir """
    for src_field, tgt_field in (('form', 'formctx'), ('xpos', 'xposctx')):
        this_data.update_value(
            field = tgt_field,
            values = this_data.get_contexts(src_field, size=context))

    """ Save this data to the model directory for reproducibility and
    ease of use """
    conllu_ext = os.path.join(Paths.models, prefix, 'conllu', f'{data_type}.conllu')
    this_data.write_file(conllu_ext)
                
    """ Generate training data """
    tagger_path = os.path.join(
        Paths.models, prefix, 'tagger', 'traindata')
    lemmatizer_path = os.path.join(
        Paths.models, prefix, 'lemmatizer', 'traindata')

    """ Define target and source files for NN-training data """
    pos_src_fn = os.path.join(tagger_path, f'{data_type}.src')
    pos_tgt_fn = os.path.join(tagger_path, f'{data_type}.tgt')
    lem_src_fn = os.path.join(lemmatizer_path, f'{data_type}.src')
    lem_tgt_fn = os.path.join(lemmatizer_path, f'{data_type}.tgt')

    logger('   + Building tagger and lemmatizer training sets')
    
    """ Build training data """
    with open(pos_src_fn, 'w', encoding='utf-8') as pos_src,\
         open(pos_tgt_fn, 'w', encoding='utf-8') as pos_tgt,\
         open(lem_src_fn, 'w', encoding='utf-8') as lem_src,\
         open(lem_tgt_fn, 'w', encoding='utf-8') as lem_tgt:

        fields = ('form', 'lemma', 'xpos', 'formctx', 'xposctx')
        for data in this_data.get_contents(*fields):
            form, lemma, xpos, formctx, xposctx = data
            pos_src.write(PP.make_tagger_src(formctx, context=context) + '\n')
            pos_tgt.write(xpos + '\n')
            lem_src.write(PP.make_lem_src(form, xposctx) + '\n')
            lem_tgt.write(PP.get_chars_lemma(lemma) + '\n')
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
            prefix, hyper)

        base_yaml.make_tagger_yaml(
            prefix, hyper)

    make_lexicon(prefix, data_type, filename)


def build_train_data(*models):
    """ Build train data from CoNLL-U files in the given
    folder.

    :param models         arbitrary number of model names that
                          correspond to file prefixes in the conllu path
    :param conllu_path    location of CoNLL-U files

    :type models          str
    :type models          str                        """
    
    filelist = [x for x in os.listdir(Paths.conllu)
                if x.endswith('.conllu') and x.startswith(tuple(models))]

    if not filelist:
        print(f'\n> Path "{Path.conllu}" does not contain'\
              ' files with given prefix')
        sys.exit(0)
    
    for filename in sorted(filelist):
        _make_training_data(os.path.join(Paths.conllu, filename))
        
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
        if model not in os.listdir(Paths.models):
            print(f'> Run build_training_data({model}) before training.')
            sys.exit(0)

        ## TODO: use os.path.join instead of string formatting
        model_path = os.path.join(Paths.models, model)
        for yaml in (x for x in os.listdir(model_path) if x.endswith('.yaml')):
            os.system(f'{python_path}python {onmt_path}build_vocab.py '\
                      f'-config {model_path}/{yaml} -n_sample -1 '\
                      f'-num_threads 2')
            os.system(f'{python_path}python {onmt_path}train.py '\
                      f'-config {model_path}/{yaml} {gpu}')
            pass
        _rename_model(model, 'lemmatizer')
        _rename_model(model, 'tagger')


if __name__ == "__main__":
    prefix = 'urartian0'
    models = parse_prefix(prefix)
    build_train_data(*models)
    #train_model('a', 'b')#*models)
    pass

