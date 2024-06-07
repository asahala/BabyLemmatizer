#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import os
import sys
import train_pipeline
import evaluate_models
#import conllutools
import lemmatizer_pipeline
from command_parser import parse_prefix
from preferences import Paths, __version__, Tokenizer, Context

div = '‹<>›'*16

info =\
f"""
{div}

   BabyLemmatizer {__version__}

   A. Aleksi Sahala 2023-2024
      + https://github.com/asahala

   University of Helsinki
      + Origins of Emesal Project
      + Centre of Excellence for Ancient Near-Eastern Empires

{div}
"""

def get_args():
    """ Get commandline arguments """
    ap = ArgumentParser()
    ap.add_argument(
        '--filename', type=str)
    ap.add_argument(
        '--evaluate', type=str)
    ap.add_argument(
        '--conllu-path', type=str)
    ap.add_argument(
        '--model-path', type=str)
    ap.add_argument(
        '--evaluate-fast', type=str)
    ap.add_argument(
        '--train', type=str)
    ap.add_argument(
        '--build', type=str)
    ap.add_argument(
        '--build-train', type=str)
    ap.add_argument(
        '--tokenizer', type=int, default=0)
    ap.add_argument(
        '--lemmatizer-context', type=int, default=1)
    ap.add_argument(
        '--tagger-context', type=int, default=2)
    ap.add_argument(
        '--normalize-conllu', action='store_true')
    ap.add_argument(
        '--lemmatize', type=str)
    ap.add_argument(
        '--use-cpu', action='store_true')
    ap.add_argument(
        '--preserve-numbers', action='store_true')
    return ap.parse_args()


if __name__ == "__main__":

    print(info)
    
    args = get_args()

    """ Optional args """
    if args.conllu_path:
        Paths.conllu = args.conllu_path
    if args.model_path:
        Paths.models = args.model_path

    if args.tokenizer > 2:
        print('> Invalid tokenization setting')
        print('> Use 0 = logosyllabic, 1 = sumerian, 2 = character sequence')
        sys.exit(1)
        
    """ Complementary mandatory args """
    if args.train:
        models = parse_prefix(args.train, train=True)
        train_pipeline.train_model(
            *models, cpu=args.use_cpu)
    elif args.build:
        Tokenizer.setting = args.tokenizer
        Context.lemmatizer_context = args.lemmatizer_context
        Context.tagger_context = args.tagger_context
        models = parse_prefix(args.build, build=True)
        train_pipeline.build_train_data(
            *models)
    elif args.build_train:
        Tokenizer.setting = args.tokenizer
        Context.lemmatizer_context = args.lemmatizer_context
        Context.tagger_context = args.tagger_context        
        models = parse_prefix(args.build_train, build=True)
        train_pipeline.build_train_data(
            *models)
        train_pipeline.train_model(
            *models, cpu=args.use_cpu)
    elif args.evaluate:
        models = parse_prefix(
            args.evaluate, evaluate=True)
        evaluate_models.pipeline(
            *models, cpu=args.use_cpu)
    elif args.evaluate_fast:
         models = parse_prefix(
             args.evaluate_fast, evaluate=True)
         evaluate_models.pipeline(
             *models, cpu=args.use_cpu, fast=True)
         #elif args.normalize_conllu:
         #   conllutools.normalize_all('conllu')
    elif args.lemmatize:
        cpu = args.use_cpu
        if args.preserve_numbers:
            ignore_nums = False
        else:
            ignore_nums = True
        lemmatizer = lemmatizer_pipeline.Lemmatizer(
            args.filename,
            fast=False,
            ignore_numbers=ignore_nums)
        model = args.lemmatize
        lemmatizer.run_model(model, cpu)                                        
        
