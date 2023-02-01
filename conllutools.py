
""" BabyLemmatizer: Conll-u module                   asahala 2023

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

#make_training_data('../conllu_train/' + 'test.conllu')


class Conllu:

    """ Conll-u object """

    def __init__(self, filename):
        self.fields = ('id', 'form', 'lemma', 'upos', 'xpos',
                       'feats', 'head', 'deprel', 'deps', 'misc')
        self.data = []
        self.read_conllu(filename)

    def get_training_data(self):
        """ Iterate all lines with data in Conllu file """
        for text in self.data:
            for line in text:
                if not line['is_comment']:
                    yield line['content']
            yield None
    
    def read_conllu(self, filename):
        print(f'> Reading {filename}')
        text = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                if line.startswith('#'):
                    text.append(
                        {'is_comment': True,
                         'content': line}
                        )
                elif not line:
                    self.data.append(text)
                    text = []
                else:
                    data = zip(self.fields, line.split('\t'))
                    text.append(
                        {'is_comment': False,
                         'content': {k: v for k, v in data}}
                        )
                    
                
        

