import os
import preprocessing
import shutil

"""===========================================================
CoNLL-U i/o for BabyLemmatizer 2.0

asahala 2023
https://github.com/asahala

University of Helsinki
   Origins of Emesal Project
   Centre of Excellence for Ancient Near-Eastern Empires

==========================================================="""

ID, FORM, LEMMA, UPOS, XPOS = 0, 1, 2, 3, 4
FEATS, HEAD, DEPREL, DEPS, MISC = 5, 6, 7, 8, 9

""" End-of-unit symbol """
EOU = ('<EOU>', '<EOU>', '<EOU>')

def read_conllu(filename, only_data=False):
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.read().splitlines():
            if not only_data:
                yield line
            else:
                if line:
                    if not line.startswith('#'):
                        yield line


def get_override(filename):
    """ Parse override data from CoNLL-U file """
    yield EOU
    for line in read_conllu(filename):
        if line.startswith('#'):
            continue
        if line:
            data = line.split('\t')
            yield data[FORM], data[LEMMA], data[UPOS]
        else:
            yield EOU


def get_training_data2(filename, preprocess=None):
    """ Parse training data from CoNLL-U file
    and preprocess it

    :param filename          CoNLL-U file to parse
    :param preprocess        preprocessing pipeline

    :type filename           str
    :type preprocess         method that takes transliteration
                             as an argument (one word)

    """

    stack = []
    stack.append(EOU)
    for line in read_conllu(filename):
        if line.startswith('#'):
            continue
        if line:
            data = line.split('\t')
            if preprocess is not None:
                data[FORM] = preprocess(data[FORM])
            data[FORM] = preprocessing.get_chars(data[FORM])
            stack.append((data[FORM], data[LEMMA], data[UPOS]))
        else:
            stack.append(EOU)

        if len(stack) == 3:
            if stack[1] != EOU:
                yield tuple(stack)
            else:
                yield EOU

            stack.pop(0)


def make_conllu(final_results, source_conllu, output_conllu):
    """ Merge annotations with existing CoNLL-U file

    :param final_results        lemmatizer's final output file
    :param source_conllu        original input CoNLL-U file
    :param output_conllu        output CoNNL-U for annotations

    """
    only_data = False
    if isinstance(final_results, str):
        with open(final_results, 'r', encoding='utf-8') as f:
            results = f.read().splitlines()
    else:
        only_data = True
        results = [f'{line[2]}\t{line[3]}' for line, score in final_results]
        
    with open(source_conllu, 'r', encoding='utf-8') as f,\
         open(output_conllu, 'w', encoding='utf-8') as output:

        for line in f.read().splitlines():
            if not line:
                output.write(line + '\n')
                if not only_data:
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


def upl_to_conllu(upl_file, output):
    """ Convert unit-per-line format into CoNLL-U

    :param upl_file            upl file name
    :param output              CoNNL-u file name

    Example of the input format (line-by-line):

    šum-ma a-wi-lum
    in DUMU a-wi-lim uh₂-ta-ap-pi-id
    in-šu u-hap-pa-du
 
    """

    head = {1: '0'}
    deprel = {1: 'root'}

    with open(upl_file, 'r', encoding='utf-8') as f,\
         open(output, 'w', encoding='utf-8') as o:

        for line in f.read().splitlines():
            i = 1
            for word in line.strip().split(' '):
                hh = head.get(i, '1')
                rr = deprel.get(i, 'child')
                o.write(f'{i}\t{word}\t_\t_\t_\t_\t{hh}\t{rr}\t_\t_\n')
                i += 1
            o.write('\n')

    print(f'> File converted to CoNLL-U and saved as {output}')


def normalize_conllu(filename, output_filename):
    """ Normalizes CoNLL-U file transliteration and lemmatization """

    content = list(read_conllu(filename))

    with open(output_filename, 'w', encoding='utf-8') as f:
        for line in content:
            if line:
                line = line.split('\t')
                orig = line[1]
                orig2 = line[2]
                line[1] = line[1].replace('sz', 'š')
                line[1] = line[1].replace('SZ', 'Š')
                line[1] = line[1].replace('s,', 'ṣ')
                line[1] = line[1].replace('t,', 'ṭ')
                line[1] = preprocessing.lowercase_determinatives(line[1])
                line[1] = preprocessing.unify_h(line[1])
                line[1] = preprocessing.subscribe_indices(line[1])
                line[2] = preprocessing.unify_h(line[2])
                f.write('\t'.join(line) + '\n')
            else:
                f.write('\n')
            

def normalize_all(path):
    """ Lowercases determinatives and unifies special h with h """

    try:
        os.mkdir(os.path.join(path, 'normalized'))
    except FileExistsError:
        'huumori__huiskaus'
        pass

    files = (x for x in os.listdir(path) if x.endswith('.conllu'))
    for file in files:
        print(f'> normalizing {file}')
        fn = os.path.join(path, file)
        ofn = os.path.join(path, 'normalized', file)
        normalize_conllu(fn, ofn)


if __name__ == "__main__":
    pass
