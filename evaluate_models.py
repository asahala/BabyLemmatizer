#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os
import math
import copy
from collections import defaultdict
from collections import Counter
from command_parser import parse_prefix
from postcorrect import pipeline as PP
from preferences import Paths, Tokenizer
import postprocess
import model_api
import conllutools
import conlluplus
import cuneiformtools.tests as tests

## TODO: get rid of conllutools

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
    keys = [f' MODEL{e}' for e, x in enumerate(sorted(results.keys()), start=0)]
    print('COMPONENT', 'AVG', 'CI', '\t'.join(keys), sep='\t')
    csv.append(';'.join(
        ('#component', 'confidence_interval',
         'average', ';'.join(keys))))

    """ Collect accuracies for each evaluation category
    for each model from result dict """
    for model, data in sorted(results.items()):
        for model_type, res in data.items():
            #try:
            vf[model_type].append(res['accuracy'])
            #except KeyError:
            #    vf[model_type].append(0)
                
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

        csv.append(';'.join(
            (model_type,
             _avg_acc,
             _conf_interval,
             ';'.join(_model_acc))))

    """ Pretty print OOV rates for each model """
    _avg_oov = format(round(100 * sum(oov_rates.values())\
                            / len(oov_rates), 2), '.2f')
    _model_oov = [format(round(100*y, 2), '.2f')
                  for x, y in sorted(oov_rates.items())]
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


def evaluate(predictions, gold_standard, model, model_path):
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
    oov_path = os.path.join(model_path, 'lex', 'test-types-oov.xlit')
    oov = set()
    with open(oov_path, 'r', encoding='utf-8') as f:
        for word in f.read().splitlines():
            oov.add(word.split('\t')[0])

    """ Initialize containers for results """
    results = defaultdict(int)
    errors = defaultdict(list)
    results_oov = defaultdict(int)
    total = 0
    total_oov = 0
    skip = 0
    
    """ Compare predictions to gold standard """
    for p, g in zip(pred, gold):
        s_index = conllutools.FORM
        e_index = conllutools.XPOS+1
        score_index = conlluplus.SCORE
        
        xlit, p_lemma, p_upos, p_xpos = p.split('\t')[s_index:e_index]
        g_lemma, g_upos, g_xpos = g.split('\t')[s_index+1:e_index]

        p_score = p.split('\t')[score_index]
        
        """ Skip lacunae that are never annotated """
        if tests.is_lacuna(xlit):
            if p_xpos == 'u' and p_lemma == '_':
                skip += 1
                continue            
        
        """ Build evaluation pairs for different categories """
        eval_data = {
            'POS-tagger': (p_xpos, g_xpos),
            'Lemmatizer': (p_lemma, g_lemma),
            'Combined  ': (f'{p_lemma} {p_xpos}', f'{g_lemma} {g_xpos}')} 
        
        """ Compare OOV inputs and all inputs """
        for category, pair in eval_data.items():
            if xlit in oov:
                if pair[0] == pair[1]:
                    results_oov[category] += 1
                else:
                    results_oov[category] += 0
                
            if pair[0] == pair[1]:
                results[category] += 1
            else:
                errors[category].append((xlit, pair[0], pair[1]))

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

    """ Write error logs """
    for category, errs in errors.items():
        cat = category.lower().strip()
        with open(os.path.join(model_path, 'eval', f'errors-{cat}.tsv'),
                  'w', encoding='utf=8') as efile:
            errorfreqs = sorted([(str(v).zfill(3), *k) for k, v in Counter(errs).items()], reverse=True)
            efile.write('OOV\tFREQ\tFORM\tPRED\tGOLD\n')
            for e in errorfreqs:
                xlit = e[1]
                if xlit in oov:
                    is_oov = '+'
                else:
                    is_oov = '-'
                efile.write(is_oov + '\t' + '\t'.join(e) + '\n')
            
    """ Calculate OOV rate """
    #for k, v in results_oov.items():
    #    print(k,v)
    #if oov:
    #    oov_rate = output['Lemmatizer OOV']['total']/output['Lemmatizer']['total']
    #else:
    #    oov_rate = 0.0
    oov_rate = total_oov / total

    print(f'>NOTE: {skip} lacunae ignored') 
    return output, oov_rate
        
    
def pipeline(*models, cpu=False, fast=False):
    """ Run the whole evaluation pipeline for `models`

    :param models        model name
    :param cpu           run on CPU instead of GPU
    :param no_run        do not rerun tagger/lemmatizer
       
    :type models         str
    :type cpu            bool
    :type no_run         bool

    """

    ## TODO: simplify, too much reading and writing same files
    
    results = defaultdict(dict)
    R = defaultdict(dict)
    R_post = defaultdict(dict)
    OOV = defaultdict(int)
    OOV_post = defaultdict(int)
    
    step = 'model.pt'
    
    for model in models:

        """ Paths """
        model_path = os.path.join(Paths.models, model)
        eval_path = os.path.join(model_path, 'eval')
        tagger_path = os.path.join(model_path, 'tagger')
        lemmatizer_path = os.path.join(model_path, 'lemmatizer')
        conllu_path = os.path.join(model_path, 'conllu')
        
        """ Load Tokenizer preferences """
        Tokenizer.read(model)                
        
        """ Intermediate files """
        tagger_output = 'output_tagger.txt'
        lemmatizer_input = 'input_lemmatizer.txt'
        lemmatizer_output = 'output_lemmatizer.txt'
        final_output = 'output_final.txt'
        
        """ Ignore fast evaluation if it has not been run before """
        eval_files = set(os.listdir(eval_path))
        if tagger_output not in eval_files\
           or lemmatizer_output not in eval_files:
            print('> Ignoring --evaluate-fast:'\
                  ' tagger/lemmatizer outputs not found')
            fast = False

        """ Load test data as CoNLL-U+ object """
        this_data = conlluplus.ConlluPlus(
            os.path.join(conllu_path, 'test.conllu'),
            validate=False)

        this_data.force_value('lemma', '_')
        this_data.force_value('xpos', '_')
        this_data.force_value('upos', '_')
        
        if not fast:
            print(f'> Running model {model}')
            """ Run tagger """
            model_api.run_tagger(
                input_file = os.path.join(tagger_path, 'traindata', 'test.src'),
                model_name = os.path.join(tagger_path, step),
                output_file = os.path.join(eval_path, tagger_output),
                cpu = cpu)

            #xpos_tags = model_api.read_results(os.path.join(eval_path, tagger_output))
            #this_data.update_value('xpos', xpos_tags)
            #xposctx = this_data.get_context('xpos')
            #this_data.update_value('xposctx', xposctx)
            """ Merge tagger output with CoNLL-U+ """
            model_api.merge_tags(
                neural_net_output = os.path.join(eval_path, tagger_output),
                conllu_object = this_data,#os.path.join(lemmatizer_path, 'traindata', 'test.src'),
                output_file = os.path.join(eval_path, lemmatizer_input),
                field = 'xpos',
                fieldctx = 'xposctx')

            """ Run lemmatizer """
            model_api.run_lemmatizer(
                input_file = os.path.join(eval_path, lemmatizer_input),
                model_name = os.path.join(lemmatizer_path, step),
                output_file = os.path.join(eval_path, lemmatizer_output),
                cpu = cpu)

            """ Merge lemmatizer output with CoNLL-U+ """
            model_api.merge_tags(
                neural_net_output = os.path.join(eval_path, lemmatizer_output),
                conllu_object = this_data,#os.path.join(lemmatizer_path, 'traindata', 'test.src'),
                output_file = None,#os.path.join(eval_path, lemmatizer_input),
                field = 'lemma',
                fieldctx = None)            
            
        #""" Merge prediced results """
        #model_api.merge_to_final(
        #    tags = os.path.join(eval_path, tagger_output),
        #    lemmas = os.path.join(eval_path, lemmatizer_output),
        #    output = os.path.join(eval_path, final_output))

        if fast:
            """ Read XPOS and LEMMA tags produced by the neural net """
            xpos_tags = model_api.read_results(os.path.join(eval_path, tagger_output))
            lemmas = model_api.read_results(os.path.join(eval_path, lemmatizer_output))

            """ Merge results with the CoNLL-U file """
            #this_data = conlluplus.ConlluPlus(os.path.join(conllu_path, 'test.conllu'), validate=False)
            this_data.update_value('xpos', xpos_tags)
            this_data.update_value('lemma', lemmas)

            """ Add XPOS context field based on predictions """
            this_data.update_value('xposctx', this_data.get_contexts('xpos', size=1))
        
        #""" Force 0.0 confidence scores """
        #this_data.force_value(field='score', value=str(0.0))
        
        """ Write lemmatized/tagged file to disk """
        this_data.write_file(filename = os.path.join(eval_path, 'test_nn.conllu'))
        
        """ Write neural net results to conllu """
        #conllutools.make_conllu(
        #    final_results = os.path.join(eval_path, final_output),
        #    source_conllu = os.path.join(model_path, 'conllu', 'test.conllu'),
        #    output_conllu = os.path.join(eval_path, 'output_final.conllu'))

        """ Add contexts and rewrite """
        #fntmp = os.path.join(eval_path, 'output_final.conllu')
        #pos_contexts = conllutools.get_contexts(
        #    data = fntmp,
        #    context = 1)

        #fntmpp = os.path.join(eval_path, 'output_final.conlluplus')
        #tmp = conllutools.add_fields(
        #    fntmp, pos_contexts, conllutools.CONTEXT)
        #conllutools.write_conllu(fntmpp, tmp)
        
        """ Neural net evaluation """
        R[model], OOV[model] = evaluate(
            predictions = os.path.join(eval_path, 'test_nn.conllu'),
            gold_standard = os.path.join(model_path, 'conllu', 'test.conllu'),
            model = model,
            model_path = model_path)

        """ Run post-corrections """
        P = postprocess.Postprocessor(
            predictions = this_data,
            model_name = model)

        """ Initialize confidence scoring """
        #this_data.force_value(field='score', value=str(0.0))
        P.initialize_scores()
        P.fill_unambiguous(threshold = 0.7)
        P.disambiguate_by_pos_context(threshold = 0.7)

        this_data.force_value('xposctx', '_')
        this_data.force_value('formctx', '_')
        this_data.write_file(
            filename = os.path.join(eval_path, 'test_pp.conllu'),
            add_info = True)
        
        """ Post-correction evaluation """
        R_post[model], OOV_post[model] = evaluate(
            predictions = os.path.join(eval_path, 'test_pp.conllu'),
            gold_standard = os.path.join(model_path, 'conllu', 'test.conllu'),
            model = model,
            model_path = model_path)
                

    print('\nNeural Net Evaluation') 
    cross_validation(R, OOV)
    print('\nPost-correct Evaluation')
    cross_validation(R_post, OOV_post)

if __name__ == "__main__":
    #prefix = 'lbtest1'
    #models = parse_prefix(prefix, evaluate=True)
    #pipeline(*models, cpu=True)
    pass
