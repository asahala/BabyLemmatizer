from collections import Counter
from collections import defaultdict

""" Evaluator for Neural BabyLemmatizer         asahala 2021

Compares results with the gold test data. This script assumes
that that only one option is produced. 

"""

def read_conllu(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.read().splitlines():
            if line:
                yield line.split('\t')
            else:
                yield

def make_vocab(filename):
    vocabulary = set()
    for line in read_conllu(filename):
        if line:
            vocabulary.add(line[1])
    return frozenset(vocabulary)

def count_words(filename):

    def read(filename):
        for line in read_conllu(filename):
            if line:
                yield line[1]

    return Counter(read(filename))

def get_type(wordform):
    if wordform.islower():
        return 'syllabic'
    return 'logogram'


def compare2(pred, gold, vocabulary, freqs, full_report=False):
    """ Evaluate conllu by part-of-speech
 
    :param pred              filled output from neural parser
    :param gold              test data in conllu format
    :param vocabulary        vocabulary from training data
    :param full_report       verbose level, if True, prints
                             all words, if False, prints only
                             a summary """
    
    def calc_acc(a, b):
        if b == 0:
            return '--'
        else:
            return str(round(a/b, 3))

    mism_conf = []
    match_conf = []

    mismatches = defaultdict(list)
    mism_counts = {'total': defaultdict(int),
                   'syllabic': defaultdict(int),
                   'logogram': defaultdict(int),
                   'syllabic-oov': defaultdict(int),
                   'logogram-oov': defaultdict(int)}
    match_counts = {'total': defaultdict(int),
                   'syllabic': defaultdict(int),
                   'logogram': defaultdict(int),
                   'syllabic-oov': defaultdict(int),
                   'logogram-oov': defaultdict(int)}

    lacunae = 0
    numbers = 0
    divs = 0

    # sanity check
    succ = {'all': 0, 'pos': 0}

    for p, g in zip(pred, gold):
        """ Ignore empty lines in conllu """
        if p is not None:
            p_xlit = p[1]
            p_lemma = p[2]
            g_lemma = g[2]
            p_pos = p[3]
            g_pos = g[3]


            """ Ignore lacunae and numerals because Oracc does not
            lemmatize them! """
            if g_pos in 'n':
                numbers += 1
                #continue
            if g_pos in 'u':
                lacunae += 1
                #continue
            if g_pos == '_':
                divs += 1
                continue
            if len(g_pos) == 2 and g_pos.endswith('PN'):
                pass
                #continue
            
            """ Uncomment to see results with OOV supposedly
            fixed by hand """
            #if p[-1] == '0.0' or p[-1] == '1.0':
            #    continue

            wordtype = get_type(p_xlit)
            oov = p_xlit not in vocabulary

            if oov:
                key = wordtype + '-oov'
            else:
                key = wordtype

            """ Make pretty-printed line for full report """
            entry = '{:<5d} {:<20s} {:<12s} {:<12s} {:<5s} {:<8s}'\
                    .format(freqs[p_xlit], p_xlit, p_lemma, g_lemma, str(oov), wordtype)

            if p_lemma != g_lemma:
                mismatches[p_pos].append(entry)
                mism_counts['total'][p_pos] += 1
                mism_counts[key][p_pos] += 1
                mism_conf.append(p[-1])
                if p_pos not in match_counts[key].keys():
                    match_counts[key][p_pos] = 0
                if p_pos not in match_counts['total'].keys():
                    match_counts['total'][p_pos] = 0
                    
            else:
                #if p[-1] == '0.0':
                #    print(p[1], p_lemma, g_lemma, sep='\t')
                match_counts['total'][p_pos] += 1
                match_counts[key][p_pos] += 1
                match_conf.append(p[-1])


            if p_pos == g_pos:
                succ['pos'] += 1
                if p_lemma == g_lemma:
                    succ['all'] += 1
            else:
                pass
                #print(p_pos, g_pos, p_lemma, g_lemma)

            #if p_lemma == g_lemma:
            #    if p_pos != g_pos:
            #        print('\t'.join(p))
            #        print('\t'.join(g))
            #        print('\n')
                    

    if full_report:
        print('Lemmatization accuracy')
        print('POS\tNUM\tTOTAL\tXLIT\tPRED\tGOLD\tOOV\tTYPE')
        for k, v in mismatches.items():
            counts = sorted(Counter(v).items(),
                           reverse=True, key=lambda item: item[1])
            for entries in counts:
                print('{:<7s} {:<4d} {}'.format(k, entries[-1], entries[0]))
    else:
        keys = ['syllabic', 'syllabic-oov', 'logogram', 'logogram-oov']

        print('-'*80)
        print('{:<8s} {:<5s} {:<6s} {:<15s} {:<15s} {:<15s} {:<15s}'.\
              format('POS', 'SUM', 'ACC', 'SYLL-IV', 'SYL-OOV', 'LOG-IV', 'LOG-OOV'))
        print('-'*80)

        overall_count = 0
        overall_matches = 0

        overall_count_by_cat = [0, 0, 0, 0]
        overall_matches_by_cat = [0, 0, 0, 0]

        for pos, count in sorted(match_counts['total'].items(),
                           reverse=True, key=lambda item: item[1]):

            """ Total words by POS regardless of category """
            total_counts = count + mism_counts['total'][pos]
            total_acc = str(round(count / total_counts, 3))

            overall_count += total_counts
            overall_matches += count

            """ Accuracies by category (syllabic, logogram etc. """
            total_by_cat = [match_counts[key][pos]\
                              + mism_counts[key][pos] for key in keys]
            matches_by_cat = [match_counts[key][pos] for key in keys]
            acc_by_category = [calc_acc(a,b) + ' ({})'.format(b) for a,b in zip(matches_by_cat, total_by_cat)]

            for i, c in enumerate(total_by_cat):
                overall_count_by_cat[i] += c
            
            for i, c in enumerate(matches_by_cat):
                overall_matches_by_cat[i] += c

            #print(total_counts, total_acc, acc_by_category)
            print('{:<8s} {:<5d} {:<6s} {:<15s} {:<15s} {:<15s} {:<15s}'\
                  .format(pos,
                          total_counts,
                          total_acc,
                          *acc_by_category))

        overall_acc = [calc_acc(a,b) + ' ({})'.format(b) for a,b in
                       zip(overall_matches_by_cat, overall_count_by_cat)]

        print('-'*80)
        print('{:<8s} {:<5d} {:<6s} {:<15s} {:<15s} {:<15s} {:<15s}'\
              .format('TOTAL',
                     overall_count,
                     str(round(overall_matches/overall_count, 3)),
                     *overall_acc))
        print('-'*80)
        print('Total word mass includes %i lacunae, %i numbers and %i rulings (%i total)'\
              % (lacunae, numbers, divs, divs+lacunae+numbers))
        print('Note that correctly labeled lacunae and numbers are considered as correct lemmata')
        print('-'*80)

        mism_conf = Counter(mism_conf)
        match_conf = Counter(match_conf)
        print('Accuracy by confidence score:\n')
        print('score\trate\tinputs\terrors')
        for key in sorted(set(mism_conf + match_conf)):
            total = mism_conf.get(key, 0) + match_conf.get(key, 0.001)
            rate = match_conf.get(key, 0) / total
            print(key, round(rate,3), total, mism_conf[key], sep='\t')
        print('-'*80)
        print(succ['all'] / overall_count, '(pos+lemma match)', sep=' ')
        print(succ['pos'] / overall_count, '(pos match)', sep=' ')
        print('-'*80)
        #print(SUCCESS/(SUCCESS+FAIL))

        
'''
""" Training data vocabulary for finding OOVs """
vocabulary = make_vocab('baby-train.conllu')

""" Read gold test data and predictions (both in conllu) """
gold = read_conllu('baby-minimized-test.conllu')
pred = read_conllu('baby-minimized-output-final.txt')
compare2(pred, gold, vocabulary, full_report=True)'''

#gold = read_conllu('babylonian-transl-mini-test.conllu')
#pred = read_conllu('output_transl_mini.txt')
#compare2(pred, gold, make_vocab('babylonian-transl-mini-train.conllu'))
