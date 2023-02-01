#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os
import math
from collections import defaultdict

""" ===========================================================
Evaluation pipeline for BabyLemmatizer 2

asahala 2023
https://github.com/asahala

University of Helsinki
   Origins of Emesal Project
   Centre of Excellence for Ancient Near-Eastern Empires

=========================================================== """

""" Paths must end with '/'. I recommend creating a virtual
environment (python-env) for OpenNMT with its required
dependencies. """

py_path = '/projappl/clarin/onmt/OpenNMT/bin/'
onmt_path = './OpenNMT-py/onmt/bin/'


def run_tagger(model): 
    input_file = f'./models/{model}/tagger/traindata/test.src'
    model_name = f'./models/{model}/tagger/model_step_35000.pt'
    output_file = f'./models/{model}/eval/output_tagger.txt'
    command = f"{py_path}python {onmt_path}translate.py -model {model_name} -src {input_file} -output {output_file} -gpu 0 -min_length 1"
    os.system(command)


def run_lemmatizer(model):
    input_file = f'./models/{model}/eval/input_lemmatizer.txt'
    model_name = f'./models/{model}/lemmatizer/model_step_35000.pt'
    output_file = f'./models/{model}/eval/output_lemmatizer.txt'
    command = f"{py_path}python {onmt_path}translate.py -model {model_name} -src {input_file} -output {output_file} -gpu 0 -min_length 1"
    os.system(command)


def merge_tags(model):
    """ This function merges Tagger output with lemmatizer test data
    to create input for lemmatizer evaluation """
    
    tagged = f'./models/{model}/eval/output_tagger.txt'
    lemma_test = f'./models/{model}/lemmatizer/traindata/test.src'
    output = f'./models/{model}/eval/input_lemmatizer.txt'

    def filter_pos(string):
        xlit = string.split(' PREV')[0]
        return xlit
    
    with open(tagged, 'r', encoding='utf-8') as t_file,\
         open(lemma_test, 'r', encoding='utf-8') as l_file,\
         open(output, 'w', encoding='utf-8') as o_file:

        lemmas = (filter_pos(x) for x in l_file.read().splitlines())
        #tags = (f'UPOS={x}' for x in t_file.read().splitlines())


        tag_segments = []

        stack = ['<EOU>']
        for tag in t_file.read().splitlines():
            if tag == '<SEG>':
                tag = '<EOU>'
            stack.append(tag)
            if len(stack) == 3:
                #if stack[1] != '<EOU>':
                tag_segments.append('PREV={} UPOS={} NEXT={}'.format(*stack))
                stack.pop(0)

        tag_segments.append('PREV={} UPOS={} NEXT=<EOU>'.format(*stack))
        
        for lemma, pos in zip(lemmas, tag_segments):
            if lemma == '<SEG>':
                o_file.write(lemma + '\n')
            else:
                o_file.write(f'{lemma} {pos}\n')
            


def _merge(tags, lemmas, output):
    """ General file merger """
    with open(tags, 'r', encoding='utf-8') as t_file,\
         open(lemmas, 'r', encoding='utf-8') as l_file,\
         open(output, 'w', encoding='utf-8') as o_file:

        combined = zip(l_file.read().splitlines(),
                       t_file.read().splitlines())
        
        for lemma, pos in combined:
            o_file.write(f'{lemma}\t{pos}\n') 


def merge_to_final(model):
    """ This function merges Tagger and Lemmatizer output and
    creates a gold standard based on test samples in the training
    data """

    _merge(f'./models/{model}/eval/output_tagger.txt',
           f'./models/{model}/eval/output_lemmatizer.txt',
           f'./models/{model}/eval/output_final.txt')

    _merge(f'./models/{model}/tagger/traindata/test.tgt',
           f'./models/{model}/lemmatizer/traindata/test.tgt',
           f'./models/{model}/eval/gold.txt')


def evaluate(model):
    tagger_res = f'./models/{model}/eval/output_tagger.txt'
    tagger_tgt = f'./models/{model}/tagger/traindata/test.tgt'

    lemmatizer_res = f'./models/{model}/eval/output_lemmatizer.txt'
    lemmatizer_tgt = f'./models/{model}/lemmatizer/traindata/test.tgt'

    combined_res = f'./models/{model}/eval/output_final.txt'
    combined_tgt = f'./models/{model}/eval/gold.txt'
    
    def compare(source, target):
        correct = 0
        incorrect = 0
        
        with open(source, 'r', encoding='utf-8') as pred,\
             open(target, 'r', encoding='utf-8') as gold:
            
            combined = zip(pred.read().splitlines(), gold.read().splitlines())

            for result in (p == g for p, g in combined if g != '<SEG>'):
                if result:
                    correct += 1
                else:
                    incorrect +=1
                       
        return {'accuracy': correct/(correct+incorrect),
                'correct': correct,
                'incorrect': incorrect,
                'total': correct+incorrect}

    tagger_results = compare(tagger_res, tagger_tgt)
    lemmatizer_results = compare(lemmatizer_res, lemmatizer_tgt)
    combined_results = compare(combined_res, combined_tgt)
    #print(tagger_results)
    #print(lemmatizer_results)
    return tagger_results, lemmatizer_results, combined_results


def cross_validation(results):
    """ Calculate confidence interval for n-fold cross-validation """
    
    n = len(results)
    vf = defaultdict(list)

    print(' '*10, 'aver.', '\t'.join(results), 'conf. int', sep='\t')
    
    for model, data in results.items():
        for model_type, res in data.items():
            vf[model_type].append(res['accuracy'])
            
    for model_type, acc in vf.items():
        average = sum(acc) / len(acc)
        deviation = [(x-average)**2 for x in acc]
        variance = sum(deviation) / max((n-1), 1)
        std_deviation = math.sqrt(variance)
        conf_interval = round(1.96 * (std_deviation / math.sqrt(n)) * 100, 2)

        print(model_type, round(average*100, 2), '\t'.join(str(round(x*100, 2)) + '%' for x in acc), f'±{conf_interval}%', sep='\t')      
    

def make_conllu(model):

    combined_res = f'./models/{model}/eval/output_final.txt'
    conllu = f'./conllu/{model}-test.conllu'
    lemmatized_conllu = f'./models/{model}/eval/output_final.conllu'

    with open(combined_res, 'r', encoding='utf-8') as f:
        results = f.read().splitlines()
    
    with open(conllu, 'r', encoding='utf-8') as f,\
         open(lemmatized_conllu, 'w', encoding='utf-8') as output:

        for line in f.read().splitlines():
            if not line:
                output.write(line + '\n')
            elif line.startswith('#'):
                output.write(line + '\n')
            else:
                line = line.split('\t')
                lemma, pos = results.pop(0).split('\t')
                line[2] = lemma
                line[3] = pos
                line[4] = pos
                output.write('\t'.join(line) + '\n')

                
def pipeline(*models):
    """ Run the whole evaluation pipeline for `models`

    :param models               model name
    :type models                str

    """

    results = defaultdict(dict)

    
    for model in models:
        print(f'> Running model {model}')
        run_tagger(model)
        merge_tags(model)
        run_lemmatizer(model)
        merge_to_final(model)
        tagger_res, lemmatizer_res, combined_res = evaluate(model)
        results[model] = {'pos-tagger': tagger_res,
                          'lemmatizer': lemmatizer_res,
                          'combined  ': combined_res}
        make_conllu(model)
        
    cross_validation(results)
    

pipeline('lbtest1', 'lbtest2', 'lbtest3', 'lbtest4', 'lbtest5')
#pipeline('lbtest1')
#merge_tags('lbtest1')

#data = {'lbtest1': {'pos-tagger': {'accuracy': 0.971, 'correct': 56266, 'incorrect': 1708, 'total': 57974}, 'lemmatizer': {'accuracy': 0.934, 'correct': 54167, 'incorrect': 3807, 'total': 57974}}, 'lbtest2': {'pos-tagger': {'accuracy': 0.971, 'correct': 55901, 'incorrect': 1667, 'total': 57568}, 'lemmatizer': {'accuracy': 0.938, 'correct': 53977, 'incorrect': 3591, 'total': 57568}}, 'lbtest3': {'pos-tagger': {'accuracy': 0.97, 'correct': 49777, 'incorrect': 1563, 'total': 51340}, 'lemmatizer': {'accuracy': 0.933, 'correct': 47904, 'incorrect': 3436, 'total': 51340}}, 'lbtest4': {'pos-tagger': {'accuracy': 0.971, 'correct': 49461, 'incorrect': 1490, 'total': 50951}, 'lemmatizer': {'accuracy': 0.932, 'correct': 47475, 'incorrect': 3476, 'total': 50951}}, 'lbtest5': {'pos-tagger': {'accuracy': 0.97, 'correct': 53050, 'incorrect': 1630, 'total': 54680}, 'lemmatizer': {'accuracy': 0.936, 'correct': 51178, 'incorrect': 3502, 'total': 54680}}}
#cross_validation(data)

#merge_to_final('lbtest1')
