#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import os
import train_pipeline
import evaluate_models
#import conllutools
import lemmatizer_pipeline
from command_parser import parse_prefix
from preferences import Paths, __version__

div = '‹<>›'*16

info =\
f"""
{div}

   BabyLemmatizer {__version__}

   A. Aleksi Sahala 2023
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
        '--normalize-conllu', action='store_true')
    ap.add_argument(
        '--lemmatize', type=str)
    ap.add_argument(
        '--lemmatize-fast', type=str)
    ap.add_argument(
        '--use-cpu', action='store_true')
    return ap.parse_args()


if __name__ == "__main__":

    print(info)
    
    args = get_args()

    """ Optional args """
    if args.conllu_path:
        Paths.conllu = args.conllu_path
    if args.model_path:
        Paths.models = args.model_path
        
    """ Complementary mandatory args """
    if args.train:
        models = parse_prefix(args.train)
        train_pipeline.train_model(
            *models, cpu=args.use_cpu)
    elif args.build:
        models = parse_prefix(args.build, build=True)
        train_pipeline.build_train_data(
            *models)
    elif args.build_train:
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
        lemmatizer = lemmatizer_pipeline.Lemmatizer(
            args.filename,
            fast=False)
        model = args.lemmatize
        lemmatizer.run_model(model, cpu)
    elif args.lemmatize_fast:
        cpu = args.use_cpu
        lemmatizer = lemmatizer_pipeline.Lemmatizer(
            args.filename,
            fast=True)
        model = args.lemmatize
        lemmatizer.run_model(model, cpu)
                                        
        
