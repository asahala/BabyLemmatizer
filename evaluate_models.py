#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os
import math
import copy
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

def cross_validation(results):
    """ Calculate confidence interval for n-fold cross-validation """
    
    n = len(results)
    vf = defaultdict(list)

    print(' '*16, 'aver.', '\t'.join(results), 'conf. int', sep='\t')
    
    for model, data in results.items():
        for model_type, res in data.items():
            vf[model_type].append(res['accuracy'])
            
    for model_type, acc in vf.items():
        average = sum(acc) / len(acc)
        deviation = [(x-average)**2 for x in acc]
        variance = sum(deviation) / max((n-1), 1)
        std_deviation = math.sqrt(variance)
        conf_interval = round(1.96 * (std_deviation / math.sqrt(n)) * 100, 2)

        print(model_type, round(average*100, 2), '\t'.join(str(round(x*100, 2)) for x in acc), f'±{conf_interval}', sep='\t')      
    

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


def evaluate(predictions, gold_standard, model):
    """ Model evaluator. Returns dictionary of results in various
    categories.

    :param predictions          prediction CoNLL-U file path
    :param gold                 gold CoNLL-U file path
    :param model                model name """

    def norm_key(key):
        if len(key) < 16:
            key = key + ' '*(16 - len(key))
        return key

    pred = conllutools.read_conllu(predictions, only_data=True)
    gold = conllutools.read_conllu(gold_standard, only_data=True)

    """ Read OOV transliterations """
    oov_path = os.path.join('models', model, 'override', 'test-types-oov.xlit')
    oov = set()
    with open(oov_path, 'r', encoding='utf-8') as f:
        for word in f.read().splitlines():
            oov.add(word.split('\t')[0])

    results = defaultdict(int)
    results_oov = defaultdict(int)
    total = 0
    total_oov = 0

    """ Comparator """
    for p, g in zip(pred, gold):
        xlit, p_lemma, p_pos = p.split('\t')[conllutools.FORM:conllutools.UPOS+1]
        g_lemma, g_pos = g.split('\t')[conllutools.LEMMA:conllutools.UPOS+1]

        """ Build evaluation pairs for different categories """
        eval_data = {'tagger': (p_pos, g_pos),
                     'lemmatizer': (p_lemma, g_lemma),
                     'combined': (f'{p_lemma} {p_pos}', f'{g_lemma} {g_pos}')} 

        for category, pair in eval_data.items():
            if xlit in oov:
                if pair[0] == pair[1]:
                    results_oov[category] += 1
                
            if pair[0] == pair[1]:
                results[category] += 1

        """ Calculate totals """
        total += 1
        if xlit in oov:
            total_oov += 1

    output = defaultdict(dict)
    for category, correct in results.items():
        category = norm_key(category)
        output[category] = {'accuracy': correct/total,
                            'correct': correct,
                            'incorrect': total-correct,
                            'total': total}
        
    for category, correct in results_oov.items():
        category = norm_key(category + ' OOV')
        output[category] = {'accuracy': correct/total_oov,
                            'correct': correct,
                            'incorrect': total_oov-correct,
                            'total': total_oov}
    return output
        
    
def pipeline(*models, cpu):
    """ Run the whole evaluation pipeline for `models`

    :param models               model name
    :type models                str

    """
    
    results = defaultdict(dict)
    R = defaultdict(dict)

    step = 'model.pt'
    
    for model in models:

        print(f'> Running model {model}')

        """
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

        """
        
        # Merge prediced results
        model_api.merge_to_final(tags = f'./models/{model}/eval/output_tagger.txt',
                                 lemmas = f'./models/{model}/eval/output_lemmatizer.txt',
                                 output = f'./models/{model}/eval/output_final.txt')

        # Make gold standard
        model_api.merge_to_final(tags = f'./models/{model}/tagger/traindata/test.tgt',
                                 lemmas = f'./models/{model}/lemmatizer/traindata/test.tgt',
                                 output = f'./models/{model}/eval/gold.txt')
        
        conllutools.make_conllu(
            final_results = f'./models/{model}/eval/output_final.txt',
            source_conllu = f'./models/{model}/conllu/test.conllu',
            output_conllu = f'./models/{model}/eval/output_final.conllu')


        R[model] = evaluate(predictions = f'./models/{model}/eval/output_final.conllu',
                            gold_standard = f'./models/{model}/conllu/test.conllu',
                            model = model)

        model_api.assign_confidence_scores(model)

    print(f' ===== {step} =====')
    cross_validation(R)
    

if __name__ == "__main__":
    prefix = 'lbtest1'
    models = parse_prefix(prefix, evaluate=True)
    pipeline(*models, cpu=True)
