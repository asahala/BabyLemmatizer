import preprocessing

""" BabyLemmatizer: Conll-u module

asahala 2023

"""

ID, FORM, LEMMA, UPOS, XPOS = 0, 1, 2, 3, 4
FEATS, HEAD, DEPREL, DEPS, MISC = 5, 6, 7, 8, 9

EOU = ('<EOU>', '<EOU>', '<EOU>')

def read_conllu(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.read().splitlines():
            yield line

def get_training_data(filename):
    """ Builds training data for BabyLemmatizer. Output format
    is a generator object consisting of tuples

        (transliteration, lemma, part-of-speech)

    Each unit of text is separated with end-of-unit symbol. """

    yield EOU
    for line in read_conllu(filename):
        if line.startswith('#'):
            continue
        if line:
            data = line.split('\t')
            yield data[FORM], data[LEMMA], data[UPOS]
        else:
            yield EOU


def get_lemmatizer_input(filename):
    """ """

    yield EOU[0]
    for line in read_conllu(filename):
        if line.startswith('#'):
            continue
        if line:
            data = line.split('\t')
            yield data[FORM]
        else:
            yield EOU[0]

#make_training_data('../conllu_train/' + 'test.conllu')


def get_training_data2(filename, preprocess=None):
    """ DOC """

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

    with open(final_results, 'r', encoding='utf-8') as f:
        results = f.read().splitlines()

    with open(source_conllu, 'r', encoding='utf-8') as f,\
         open(output_conllu, 'w', encoding='utf-8') as output:

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


def upl_to_conllu(upl_file, output):
    """ Convert word per line format into CoNLL-u

    :param wpl_file            wpl file name
    :param output              CoNNL-u file name

    WPL file is a file that has exactly one word per line.
    Segment, e.g. line or sentence boundaries are separated
    with an empty line. E.g. if we split text by line, the
    text

    1. be-el bi-tim
    2. LUGAL bi-tim

    would look in WPL as

    be-el
    bi-tim

    LUGAL
    bi-tim

    """

    head = {1: 0}
    deprel = {1: 'root'}

    with open(upl_file, 'r', encoding='utf-8') as f,\
         open(output, 'w', encoding='utf-8') as o:

        i = 1
        for line in f.read().splitlines():
            for word in line.strip().split(' '):
                n = head.get(i)
                r = deprel.get(i, 'child')
                o.write(f'{i}\t{word}\t_\t_\t_\tempty\t{n}\t{r}\t_\t_\n')
                i += 1
            i = 1
            o.write('\n')

    print(f'> File converted to CoNLL-U and saved as {output}')

