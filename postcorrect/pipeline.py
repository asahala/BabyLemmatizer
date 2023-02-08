import re
import os
#import postcorrect.vrt_to_conllu as vrt2conllu
import postcorrect.minimize as minimize
import postcorrect.unminimize as unminimize
import postcorrect.baseline as baseline
import postcorrect.evaluate as evaluate
import postcorrect.disambiguator as disambiguator
import postcorrect.postcorrect as postcorrect
import postcorrect.logogram_analyzer as LA

""" Neural BabyLemmatizer data generation and evaluation pipeline
                                                  -- asahala 2021

  make_training_data()

      Creates train/dev/test sets from VRT data. Requires
         SOURCE_VRT        (str) path to VRT file
         OUT_DATA_PATH     (str) path to save data
         FILE_PREFIX       (str) prefix for train/dev/test
         LANG_REGEX        (re)  regex to match languages in
                                 VRT files
         MINIMIZE          (bool) use quasi-transcription

  evaluate_data()

      Enhances and evaluates BabyLemmatizer output. Give
      lemmatizer output in CONLLU as produced by TurkuNLP.  

"""

SOURCE_VRT = '../corpora/achem_traindata.vrt'
OUT_DATA_PATH = '../data/'
FILE_PREFIX = ''
LANG_REGEX = re.compile('.+')
MINIMIZE = False

DIV = '='*63
fn = OUT_DATA_PATH + FILE_PREFIX


def make_training_data(filename=fn, minimize_=MINIMIZE, lang_regex=LANG_REGEX):
    print(DIV)
    vrt2conllu.LANG_REGEX = lang_regex
    vrt2conllu.ERRORFILE = '../corpora/oracc-errors.tsv'
    vrt2conllu.LOGFILE = FILE_PREFIX + '-changes.log'
    trees = vrt2conllu.process(SOURCE_VRT)
    vrt2conllu.save_data(trees, filename)

    if minimize_:
        print(DIV)
        print('> Quasi-transcribing...')
        minimize.process(filename)

    '''
    print(DIV)
    print('> Calculating baseline accuracy (most common lemma)...')
    if minimize_:
        lookup = baseline.read_train(filename+'-minimized-train.conllu')
        baseline.lemmatize_test(filename+'-minimized-test.conllu', lookup)
    else:
        lookup = baseline.read_train(filename+'-train.conllu')
        baseline.lemmatize_test(filename+'-test.conllu', lookup)
    print(DIV)
    print('> Train/dev/test data ready. You may now train the lemmatizer.')
    print(DIV)
    '''


def evaluate_data(lemmatizer_output):
    print(DIV)
    print('> Reversing quasi-transcription...')
    xlit_file = fn + '.xlit'
    #xlit_file = '../data/enuma.xlit'
    unamb, lemmadict = unminimize.get_unamb2(fn+'-train.conllu',
                                             threshold=0.4)
    print('> Using lemma dictionary to replace unambiguous lemmata...')
    output = unminimize.fill_unamb(lemmatizer_output, xlit_file,
                                   unamb, lemmadict)
    
    """ Add context information to FEATS column """
    print('> Attempting to disambiguate logograms...')
    output = disambiguator.add_context(list(output), 'pos-map.json')

    """ Disambiguate lemmata """
    traindata = disambiguator.readfile(fn+'-train.conllu')
    train_ctx = disambiguator.add_context(traindata,
                                          'pos-map.json',
                                          simplify=False)
    ctx_data = disambiguator.get_context(train_ctx)
    output = (disambiguator.disambiguate(line, ctx_data) for line in output)

    """ Find logograms that are likely impossible to lemmatize
    i.e. those that the neural net never saw before) and mark
    them with a confidence score of 0.0 """
    traindata_logograms = LA.get_logograms(traindata)
    output = LA.mark_oov_logograms(output, traindata_logograms)
    
    """ Write to file """
    unminimize.write_conllu(lemmatizer_output+'.final', output)

    print('> Evaluating...')
    """ Count freqs from test data for eval """
    freqs = evaluate.count_words(fn+'-test.conllu')
    vocabulary = evaluate.make_vocab(fn+'-train.conllu')        
    gold = evaluate.read_conllu(fn+'-test.conllu')
    pred = evaluate.read_conllu(lemmatizer_output + '.final')
    evaluate.compare2(pred, gold, vocabulary, freqs, full_report=False)

    print('BASELINE: ')
    lookup, l2 = baseline.read_train(fn+'-train.conllu')
    baseline.lemmatize_test(fn+'-test.conllu', lookup)
    baseline.postag_test(fn+'-test.conllu', l2)

def evaluate_unseen(lemmatizer_output, gold_file, master,
                    override=True, disambiguate=True):

    xlits = []
    with open(lemmatizer_output, 'r', encoding='utf-8') as f:
        for x in f.read().splitlines():
            if x:
                xlit = x.split('\t')[1]
            else:
                xlit = ''
            xlits.append(xlit)

    with open('tmp.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(xlits))

    xlit_file = 'tmp.txt'
    
    unamb, lemmadict = unminimize.get_unamb2(master,
                                             threshold=0.4)

    output = unminimize.fill_unamb(lemmatizer_output, xlit_file,
                                       unamb, lemmadict, override)
        
    """ Postcorrections """
    #output = postcorrect.process(output)
    
    output = disambiguator.add_context(list(output), 'pos-map.json')

    """ Add contexts and disambiguate """
    traindata = disambiguator.readfile(master)

    if disambiguate:
        train_ctx = disambiguator.add_context(traindata,
                                              'pos-map.json',
                                              simplify=False)
        ctx_data = disambiguator.get_context(train_ctx)

        output = (disambiguator.disambiguate(line, ctx_data) for line in output)

    """ Find logograms that are likely impossible to lemmatize
    i.e. those that the neural net never saw before) and mark
    them with a confidence score of 0.0 """
    traindata_logograms = LA.get_logograms(traindata)
    output = LA.mark_oov_logograms(output, traindata_logograms)

    """ Postcorrections """
    #output = postcorrect.process(output)

    """ Write to file """
    unminimize.write_conllu(lemmatizer_output+'.final', output)

    print('> Evaluating...')
    """ Count freqs from test data for eval """
    freqs = evaluate.count_words(gold_file)
    vocabulary = evaluate.make_vocab(master)        
    gold = evaluate.read_conllu(gold_file)
    pred = evaluate.read_conllu(lemmatizer_output + '.final')
    evaluate.compare2(pred, gold, vocabulary, freqs, full_report=False)

    print('BASELINE: ')
    lookup, lookup_pos, lookup_comb = baseline.read_train(master)
    baseline.lemmatize_test(gold_file, lookup)
    baseline.postag_test(gold_file, lookup_pos)
    baseline.combined_test(gold_file, lookup_comb)
    
#evaluate_data('../data/baby-output.txt')
#make_training_data()
#evaluate_unseen('../data/atae-ass4-output.conllu', '../data/atae-test.conllu', '../models/assyrian/ass-master.conllu')


#atae
#evaluate_unseen('../data/atae-norm-output.txt', '../data/atae-norm-test1.conllu', '../models/assyrian/ass-master.conllu')

#trans
#evaluate_unseen('../data/babyt-output.conllu', '../data/babyt-test.conllu', '../data/babyt-train.conllu')

#evaluate_unseen('../data/ass2-output.txt', '../data/ass2-test.conllu', '../data/ass2-train.conllu')
#evaluate_unseen('../data/t_ulos.conllu', '../data/t_gold.conllu', '../data/ass-master.conllu')

def eval_atae():
    o = True
    d = True
    evaluate_unseen('../data/evaluation_2021/ass_case1/atae-test2-output.conllu',
                    '../data/evaluation_2021/ass_case1/atae-test2.conllu',
                    '../data/evaluation_2021/ass_case1/case-train.conllu',
                    override=o, disambiguate=d)


    evaluate_unseen('../data/evaluation_2021/ass_case2/atae-test2-output.conllu',
                    '../data/evaluation_2021/ass_case2/atae-test2.conllu',
                    '../data/evaluation_2021/ass_case2/case-train.conllu',
                    override=o, disambiguate=d)
#eval_atae()

def make_lb_test_data():
    INDEX = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
    for e, n in enumerate(['1', '2', '3', '4', '5']):
        FILE_PREFIX = 'lbtest' + n
        test = INDEX[e][0]
        dev = INDEX[e][1]
        print(FILE_PREFIX, test, dev)
        vrt2conllu.TEST = test
        vrt2conllu.DEV = dev
        fn = OUT_DATA_PATH + FILE_PREFIX
        make_training_data(filename=fn)
        
#make_lb_test_data()

def eval_lbtest(prefix):

    for n in '12345':
            
        override_ = True
        disamb = True

        print(f'## {prefix}{n}')
        evaluate_unseen(f'./models/{prefix}{n}/eval/output_final.conllu',#lbtest{n}-test-lem.conllu',
                        f'./models/{prefix}{n}/conllu/test.conllu',
                        f'./models/{prefix}{n}/conllu/train.conllu',
                        override=override_, disambiguate=disamb)


def eval_test(prefix, model_path):

    override_ = True
    disamb = True

    print(f'## {prefix}')
    evaluate_unseen(
        os.path.join(model_path, prefix, 'eval', 'output_final.conllu'),
        os.path.join(model_path, prefix, 'conllu', 'test.conllu'),
        os.path.join(model_path, prefix, 'conllu', 'train.conllu'),
                        override=override_, disambiguate=disamb)
       
      
#eval_lbtest('lbtest')



def test():
    override_ = True
    disamb = False

    n='2'
    print(f'## lbtest{n}')
    evaluate_unseen(f'../data/evaluation_2022/lbtest{n}/lbtest{n}-test-lem.conllu',
                        f'../data/evaluation_2022/lbtest{n}/lbtest{n}-test.conllu',
                        f'../data/evaluation_2022/lbtest{n}/lbtest{n}-test.conllu',
                        override=override_, disambiguate=disamb)

#test()

    
