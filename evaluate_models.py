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

def cross_validation(results, oov_rates):
    """ Calculate confidence interval for n-fold 
    cross-validation

    :param results        result dict from evaluation()
    :param oov_rates      oov rate dict from evaluation()

    :type results         dict
    :type oov_rates       dict  """

    
    def get_conf_interval(n, acc):
        """ Calculate confidence interval

        :param n          number of samples
        :param acc        list of results

        :type n           int
        :type acc         [float, ...]  """

        avg = sum(acc) / len(acc)
        dev = ((x - avg)**2 for x in acc)
        var = sum(dev) / max((n-1), 1)
        std_dev = math.sqrt(var)

        return round(1.96 * (std_dev / math.sqrt(n)) * 100, 2)

    
    def mark_max_value(values):
        """ Mark highest value in list with following ^ """
        if len(values) == 1:
            yield ' ' + values[0]
        else:
            high = max(format(float(x), '.2f') for x in values)
            low = min(format(float(x), '.2f') for x in values)
            for v in values:
                if v == high:
                    yield f'▲{v}'
                elif v == low:
                    yield f'▽{v}'
                else:
                    yield f' {v}'

    """ Define number of samples """
    n = len(results)
    vf = defaultdict(list)

    """ Container for data for CSV output """
    csv = []

    """ Heading for the models to be evaluated """
    keys = [f' MODEL{e}' for e, x in enumerate(results)]
    print('\n')
    print('COMPONENT', 'AVG', 'CI', '\t'.join(keys), sep='\t')
    csv.append(';'.join(
        ('#component', 'confidence_interval',
         'average', ';'.join(keys))))

    """ Collect accuracies for each evaluation category
    for each model from result dict """
    for model, data in results.items():
        for model_type, res in data.items():
            vf[model_type].append(res['accuracy'])

    """ Pretty-print results and calculate confidence
    interval for n-fold cross-validation """
    for model_type, acc in vf.items():
        ci = get_conf_interval(n, acc)       
        average = sum(acc) / len(acc)
        _avg_acc = format(round(average*100, 2), '.2f')
        _model_acc = [format(round(100*x, 2), '.2f') for x in acc]
        _conf_interval = format(ci, '.2f')
        print(model_type,
              _avg_acc,
              f'±{_conf_interval}',
              '\t'.join(mark_max_value(_model_acc)),
              sep='\t')      

        csv.append(';'.join((model_type, _avg_acc, _conf_interval, ';'.join(_model_acc))))

    """ Pretty print OOV rates for each model """
    _avg_oov = format(round(100 * sum(oov_rates.values()) / len(oov_rates), 2), '.2f')
    _model_oov = [format(round(100*y, 2), '.2f') for x, y in sorted(oov_rates.items())]
    _conf_interval = format(ci, '.2f')
    
    divlen = 26 + (len(_model_oov)+2)*7  
    print('-'*divlen)
    print('OOV input rate',
          _avg_oov,
          '    ',
          '\t'.join(mark_max_value(_model_oov)),
          sep='\t')
    
    print('\n')
    
    ## TODO: Save CSV file


def evaluate(predictions, gold_standard, model):
    """ Model evaluator. Returns dictionary of results in various
    categories.

    :param predictions          prediction CoNLL-U file path
    :param gold                 gold CoNLL-U file path
    :param model                model name 

    Returns a dictionary of the following structure:

    {eval_category1:
       {accuracy:  float,
        correct:   float,
        incorrect: float,
        total:     float},
     eval_category2:
       {...},
     ...}                                                    

    """

    def norm_key(key):
        return key
        if len(key) < 16:
            key = key + ' '*(16 - len(key))
        return key

    """ Collect predictions and gold standard """
    pred = conllutools.read_conllu(predictions, only_data=True)
    gold = conllutools.read_conllu(gold_standard, only_data=True)

    """ Read OOV transliterations """
    oov_path = os.path.join('models', model, 'override', 'test-types-oov.xlit')
    oov = set()
    with open(oov_path, 'r', encoding='utf-8') as f:
        for word in f.read().splitlines():
            oov.add(word.split('\t')[0])

    """ Initialize containers for results """
    results = defaultdict(int)
    results_oov = defaultdict(int)
    total = 0
    total_oov = 0

    """ Compare predictions to gold standard """
    for p, g in zip(pred, gold):
        xlit, p_lemma, p_pos = p.split('\t')[conllutools.FORM:conllutools.UPOS+1]
        g_lemma, g_pos = g.split('\t')[conllutools.LEMMA:conllutools.UPOS+1]

        """ Build evaluation pairs for different categories """
        eval_data = {'POS-tagger': (p_pos, g_pos),
                     'Lemmatizer': (p_lemma, g_lemma),
                     'Combined  ': (f'{p_lemma} {p_pos}', f'{g_lemma} {g_pos}')} 

        """ Compare OOV inputs and all inputs """
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

    """ Merge all results into a single dictionary """
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

    """ Calculate OOV rate """
    oov_rate = output['Lemmatizer OOV']['total']/output['Lemmatizer']['total']
        
    return output, oov_rate
        
    
def pipeline(*models, cpu):
    """ Run the whole evaluation pipeline for `models`

    :param models               model name
    :type models                str

    """
    
    results = defaultdict(dict)
    R = defaultdict(dict)
    OOV = defaultdict(int)
    
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

        """ Merge prediced results """
        model_api.merge_to_final(tags = f'./models/{model}/eval/output_tagger.txt',
                                 lemmas = f'./models/{model}/eval/output_lemmatizer.txt',
                                 output = f'./models/{model}/eval/output_final.txt')

        #""" Make gold standard """
        #model_api.merge_to_final(tags = f'./models/{model}/tagger/traindata/test.tgt',
        #                         lemmas = f'./models/{model}/lemmatizer/traindata/test.tgt',
        #                         output = f'./models/{model}/eval/gold.txt')
        
        conllutools.make_conllu(
            final_results = f'./models/{model}/eval/output_final.txt',
            source_conllu = f'./models/{model}/conllu/test.conllu',
            output_conllu = f'./models/{model}/eval/output_final.conllu')


        R[model], OOV[model] = evaluate(predictions = f'./models/{model}/eval/output_final.conllu',
                               gold_standard = f'./models/{model}/conllu/test.conllu',
                               model = model)

        model_api.assign_confidence_scores(model)

    cross_validation(R, OOV)
    

if __name__ == "__main__":
    prefix = 'lbtest1'
    models = parse_prefix(prefix, evaluate=True)
    pipeline(*models, cpu=True)
