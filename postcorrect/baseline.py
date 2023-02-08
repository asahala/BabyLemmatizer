from collections import Counter
from collections import defaultdict

""" A baseline for evaluation. The data is lemmatized by giving
each word form its most common lemma. """

def read_train(filename):
    """ Read conllu training data and return a dict lookup """
    ambiguity = 0
    lookup = defaultdict(list)
    lookup_pos = defaultdict(list)
    lookup_comb = defaultdict(list)
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.read().splitlines():
            if line:
                _, xlit, lemma, pos1, pos2, _, _, _, _, _ = line.split('\t')
                lookup[xlit].append(lemma)
                lookup_pos[xlit].append(pos1)
                lookup_comb[xlit].append(lemma+'|'+pos1)

    for k, v in lookup.items():
        ambiguity += len(v)
        lookup[k] = list(Counter(v).keys())[0]

    for k, v in lookup_pos.items():
        ambiguity += len(v)
        lookup_pos[k] = list(Counter(v).keys())[0]

    for k, v in lookup_comb.items():
        ambiguity += len(v)
        lookup_comb[k] = list(Counter(v).keys())[0]
        
    return lookup, lookup_pos, lookup_comb

#lookup = read_train('baby-train.conllu')

def lemmatize_test(filename, lookup):
    """ Lemmatize ´filename´ conllu file using ´lookup´. """
    match = 0
    mismatch = 0
    oov = 0
    mismatches = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.read().splitlines():
            if line:
                _, xlit, lemma, pos1, pos2, _, _, _, _, _ = line.split('\t')
                #if pos1 in ('PN', 'RN'):
                #    continue
                #print(pos1, pos2)
                pred = lookup[xlit]
                if pred == []:
                    oov += 1
                if pred == lemma:
                    match += 1
                else:
                    mismatches.append(xlit)
                    mismatch += 1
                    
    print('\n  match %i, mismatch %i' % (match, mismatch)) 
    print('  lem-accuracy', match / (match + mismatch), sep=': ')
    print('  OOVs', oov, sep=': ')

def postag_test(filename, lookup):
    """ Lemmatize ´filename´ conllu file using ´lookup´. """
    match = 0
    mismatch = 0
    oov = 0
    mismatches = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.read().splitlines():
            if line:
                _, xlit, lemma, pos1, pos2, _, _, _, _, _ = line.split('\t')
                #if pos1 in ('PN', 'RN'):
                #    continue
                #print(pos1, pos2)
                pred = lookup[xlit]
                if pred == []:
                    oov += 1
                if pred == pos1:
                    match += 1
                else:
                    mismatches.append(xlit)
                    mismatch += 1
                    
    print('\n  match %i, mismatch %i' % (match, mismatch)) 
    print('  pos-accuracy', match / (match + mismatch), sep=': ')
    print('  OOVs', oov, sep=': ')

#lemmatize_test('baby-test.conllu', lookup)

def combined_test(filename, lookup_comb):
    """ Lemmatize ´filename´ conllu file using ´lookup´. """
    match = 0
    mismatch = 0
    oov = 0
    mismatches = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.read().splitlines():
            if line:
                _, xlit, lemma, pos1, pos2, _, _, _, _, _ = line.split('\t')
                #if pos1 in ('PN', 'RN'):
                #    continue
                #print(pos1, pos2)
                pred = lookup_comb[xlit]
                #print(pred, xlit +'|'+pos1)
                if pred == []:
                    oov += 1
                if pred == lemma + '|' + pos1:
                    match += 1
                else:
                    mismatches.append(xlit)
                    mismatch += 1
                    
    print('\n  match %i, mismatch %i' % (match, mismatch)) 
    print('  pos+lem-accuracy', match / (match + mismatch), sep=': ')
    print('  OOVs', oov, sep=': ')

#lemmatize_test('baby-test.conllu', lookup)

