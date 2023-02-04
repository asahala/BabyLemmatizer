#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import train_pipeline
import evaluate_models
from command_parser import parse_prefix

""" ===========================================================
BabyLemmatizer 2.0

asahala 2023
https://github.com/asahala

University of Helsinki
   Origins of Emesal Project
   Centre of Excellence for Ancient Near-Eastern Empires

=========================================================== """

def get_args():
    ap = ArgumentParser()
    ap.add_argument('--evaluate', type=str)
    ap.add_argument('--train-model', type=str)
    ap.add_argument('--build-data', type=str)
    ap.add_argument('--build-train', type=str)
    return ap.parse_args()

if __name__ == "__main__":
    args = get_args()

    if args.train_model:
        models = parse_prefix(args.train_model)
        train_pipeline.train_model(*models)
    elif args.build_data:
        models = parse_prefix(args.build_data)
        train_pipeline.build_train_data(*models)
    elif args.build_train:
        models = parse_prefix(args.build_train)
        train_pipeline.build_train_data(*models)
        train_pipeline.train_model(*models)
    elif args.evaluate:
        models = parse_prefix(args.evaluate)
        evaluate_models.pipeline(*models)
