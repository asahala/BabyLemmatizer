import os
import re
import sys
from preferences import Paths

""" BabyLemmatizer 2 utils """

## TODO clean

def split_train_filename(orig_fn):
    """ Split train filename into prefix and data_type """
    prefix = re.sub('-(dev|test|train).+', '', orig_fn)
    data_type = re.sub('.+-(test|dev|train).+', r'\1', orig_fn)
    return prefix, data_type


def overwrite_prompt(prefix, files):
    """ Ask user to confirm before deleting old models

    :param prefix             input prefix notation
    :param fprefix            actual file prefix """

    np, vp = '', 's'
    if len(files) > 1:
        np, vp = vp, np
        
    prompt = f'\n> Model{np} with following name{np} exist{vp}:\n'\
            f'  + {", ".join(files)}\n'\
            f'\n> Rebuilding data or retraining the model will overwrite\n'\
            f'> and delete the old model{np}.\n\n'\
            '  Y to continue\n'\
            '  N or anything else to cancel\n\n'\
            '  Answer: '
    
    if files:
        answer = input(prompt)
        if answer == 'Y':
            pass
        else:
            print(f'\n> Model{np} {prefix} exist{vp}. Canceled by user.')
            sys.exit(1)


def parse_prefix(prefix, evaluate=False, build=False, train=False):
    """ Parse star expressions for file prefixes

    :param prefix              model name prefix
    :type prefix               str """
    """
    if build:
        for filetype in ['-train.conllu', '-dev.conllu', '-test.conllu']:
            P = os.path.join(Paths.conllu, prefix + filetype)
            print(P)
            if not os.path.isfile(P):
                print(f'> Cannot find {P}')
                print(f'> use --conllu-path=PATH and make sure you have test/dev/train data')
                sys.exit(0)
        return prefix
    """
    
    """ Check if models already exist and prompt overwrite """
    if prefix.endswith('*'):
        models = [f for f in os.listdir(Paths.models) if f.startswith(prefix[:-1])]
    else:
        models = [f for f in os.listdir(Paths.models) if f == prefix]
        
    """ Do not prompt if used for evaluation """
    if evaluate:
        if not models:
            print(f'> Model "{prefix}" does not exist in /{Paths.models}')
            print('> Use --model-path=PATH to give the correct path\n\n')
            sys.exit(0)                
        return models

    """ Test if model actually exists """
    ask_prompt = False
    if models:
        for model in models:
            tagger_path = os.path.join(Paths.models, model, 'tagger')
            lemmatizer_path = os.path.join(Paths.models, model, 'lemmatizer')
            if os.path.exists(tagger_path) or os.path.exists(lemmatizer_path):
                a = sum(1 for x in os.listdir(tagger_path) if x.endswith('.pt'))
                b = sum(1 for x in os.listdir(lemmatizer_path) if x.endswith('.pt'))
                if a + b != 0:
                    ask_prompt = True
                    break

    if ask_prompt:
        overwrite_prompt(prefix, models)

    # """ If models do not exist, check if train data exists and
    #create model name lists """
    prefixes = (split_train_filename(x)[0] for x
                in os.listdir(Paths.conllu) if x.endswith('-train.conllu'))

    if build:
        if prefix.endswith('*'):
            models = [f for f in prefixes if f.startswith(prefix[:-1])]
        else:
            models = [f for f in prefixes if f == prefix]

    if not models:
        print(f'> No training data for "{prefix}" in folder "{Paths.models}"')
        sys.exit(0)

    return models
