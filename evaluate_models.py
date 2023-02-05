#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os
import math
from collections import defaultdict
#from preferences import python_path, onmt_path
from command_parser import parse_prefix
import model_api
import conllutools

""" ===========================================================
Evaluation pipeline for BabyLemmatizer 2

asahala 2023
https://github.com/asahala

University of Helsinki
   Origins of Emesal Project
   Centre of Excellence for Ancient Near-Eastern Empires

=========================================================== """

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

            for result in (p == g for p, g in combined if p != '<EOU>'):
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
    

def make_conllu(final_results, source_conllu, output_conllu):

    with open(combined_res, 'r', encoding='utf-8') as f:
        results = f.read().splitlines()
    
    with open(conllu, 'r', encoding='utf-8') as f,\
         open(lemmatized_conllu, 'w', encoding='utf-8') as output:

        for line in f.read().splitlines():
            if not line:
                output.write(line + '\n')
                results.pop(0)
            elif line.startswith('#'):
                output.write(line + '\n')
            else:
                line = line.split('\t')
                lemma, pos = results.pop(0).split('\t')
                line[2] = lemma
                line[3] = pos
                line[4] = pos
                output.write('\t'.join(line) + '\n')

                
def pipeline(*models, cpu):
    """ Run the whole evaluation pipeline for `models`

    :param models               model name
    :type models                str

    """
    
    results = defaultdict(dict)

    step = 'model.pt'
    
    for model in models:

        print(f'> Running model {model}')

        model_api.run_tagger(input_file = f'./models/{model}/tagger/traindata/test.src',
                   model_name = f'./models/{model}/tagger/{step}',
                   output_file = f'./models/{model}/eval/output_tagger.txt',
                   cpu = cpu)
        
        model_api.merge_tags(tagged_file = f'./models/{model}/eval/output_tagger.txt',
                   lemma_input = f'./models/{model}/lemmatizer/traindata/test.src',
                   output_file = f'./models/{model}/eval/input_lemmatizer.txt')
        
        model_api.run_lemmatizer(input_file = f'./models/{model}/eval/input_lemmatizer.txt',
                       model_name = f'./models/{model}/lemmatizer/{step}',
                       output_file = f'./models/{model}/eval/output_lemmatizer.txt',
                       cpu = cpu)

        # Merge prediced results
        model_api.merge_to_final(tags = f'./models/{model}/eval/output_tagger.txt',
                                 lemmas = f'./models/{model}/eval/output_lemmatizer.txt',
                                 output = f'./models/{model}/eval/output_final.txt')

        # Make gold standard
        model_api.merge_to_final(tags = f'./models/{model}/tagger/traindata/test.tgt',
                                 lemmas = f'./models/{model}/lemmatizer/traindata/test.tgt',
                                 output = f'./models/{model}/eval/gold.txt')

        tagger_res, lemmatizer_res, combined_res = evaluate(model)
        results[model] = {'pos-tagger': tagger_res,
                          'lemmatizer': lemmatizer_res,
                          'combined  ': combined_res}  
        
        conllutools.make_conllu(
            final_results = f'./models/{model}/eval/output_final.txt',
            source_conllu = f'./models/{model}/conllu/test.conllu',
            output_conllu = f'./models/{model}/eval/output_final.conllu')

        model_api.assign_confidence_scores(model)

    print(f' ===== {step} =====')
    cross_validation(results)
    

if __name__ == "__main__":
    prefix = 'lbtest1'
    models = parse_prefix(prefix, evaluate=True)
    pipeline(*models)
