import time
import re
from collections import defaultdict

""" ============================================================
CoNLL-U+ file processor for BabyLemmatizer 2
asahala 2023
github.com/asahala/BabyLemmatizer
============================================================ """

ID, FORM, LEMMA, UPOS, XPOS = 0, 1, 2, 3, 4
FEATS, HEAD, DEPREL, DEPS, MISC = 5, 6, 7, 8, 9
ENG, NORM, LANG, FORMCTX, XPOSCTX, SCORE = 10, 11, 12, 13, 14, 15

FIELDS = {'id': 0, 'form': 1, 'lemma': 2, 'upos': 3, 'xpos': 4,
          'feats': 5, 'head': 6, 'deprel': 7, 'deps': 8,
          'misc': 9, 'norm': 11, 'lang': 12, 'formctx': 13,
          'xposctx': 14, 'score': 15}

LAST_FIELD = SCORE
SOU = '<SOU>'
EOU = '<EOU>'
UNIT_MARKERS = frozenset((SOU, EOU))


class ConlluPlus:

    """ Class for doing stuff with CoNLL-U+ files
    https://universaldependencies.org/ext-format.html
    :param filename        CoNLL-U path/filename
    :param validate        Run validator to check data integrity
    :type filename         str / path
    :type validate         bool """

    def __init__(self, filename, validate=True):
        self.validate = validate
        self.filename = filename
        self.data = []
        self.freqs = {'lemma': defaultdict(int),
                      'form': defaultdict(int),
                      'xpos': defaultdict(int)}
        self.warnings = defaultdict(list)
        self.read_file(filename)
        self.word_count = sum(len(unit) for _, unit in self.data)


    def __len__(self):
        return self.word_count
    

    def _is_valid(self, line, lineno):
        xlit = line[FIELDS['form']]
        lemma = line[FIELDS['lemma']]
        xpos = line[FIELDS['xpos']]
        lineno = str(lineno)

        identifier = f'{xlit} <> {lemma} <> {xpos}'
        
        if not line[FIELDS['id']].isdigit():
            print(f'> WARNING (line {lineno}): BabyLemmatizer expects '\
                  'exactly one word per line!')
            return False
        if line[FIELDS['lemma']] == '_':
            if 'x' not in line[FIELDS['form']]:
                self.warnings['Lemma missing for non-lacuna'].append(
                    f'{lineno.zfill(6)} | {identifier}')
            return False
        if line[FIELDS['xpos']] in ('_', 'X', 'x', 'u'):
            if 'x' not in line[FIELDS['form']]:
                self.warnings['XPOS missing for non-lacuna'].append(
                    f'{lineno.zfill(6)} | {identifier}')
            return False
        if '*' in line[FIELDS['form']]:
            self.warnings['LEMMA with star'].append(
                    f'{lineno.zfill(6)} | {identifier}')
            return False

                    
    def _iterate_fields(self, unit, *fields):
        """ General iterator for fetching data from given fields
        :param unit       CoNLL-U+ phrase/sent/text unit
        :param *fields    Names of fields to be fetched
        :type unit        iterable
        :type *fields     *str """
        
        if not fields:
            for word in unit:
                yield word
        else:
            for word in unit:
                result = []
                for index in (FIELDS[field] for field in fields):
                    result.append(word[index])
                if len(result) == 1:
                    yield result[0]
                else:
                    yield tuple(result)

             
    def read_file(self, filename):
        """ Reads and parses a CoNLL-U+ file. Forces
        additional fields for extra information 
        :param filename        filename
        :type filename         str / path  """
        
        print(f'> Parsing {filename}')
        with open(filename, 'r', encoding='utf-8') as f:
            lines = []
            comments = []
            for e, line in enumerate(f, start=1):
                line = line.strip()
                if line.startswith('#'):
                    comments.append(line)
                elif line:
                    line = line.split('\t')
                    if len(line) < LAST_FIELD:
                        line.extend(['_'] * (LAST_FIELD - len(line) + 1))

                    if self.validate:
                        is_valid = self._is_valid(line, e)
                    ## TODO: Add possibility to clean data automatically
                    lines.append(line)

                    self.freqs['lemma'][line[FIELDS['lemma']]] += 1
                    self.freqs['form'][line[FIELDS['form']]] += 1
                    self.freqs['xpos'][line[FIELDS['xpos']]] += 1
                else:
                    self.data.append((comments, lines))
                    lines = []
                    comments = []

        if self.validate:
            print('\n================================')
            print('WARNINGS')
            for k, v in self.warnings.items():
                if v:
                    print(k + ':\n================================\n')
                    for warning in v:
                        print(f'   {warning}')


    def write_file(self, filename, add_info=False):
        """ Compiles and writes a CoNLL-U+ file
        :param filename        filename
        :type filename         str / path  """

        print(f'> Writing {filename}')
        with open(filename, 'w', encoding='utf-8') as f:
            if add_info:
                f.write('# global.info = generated with BabyLemmatizer 2.0; '\
                    'github.com/asahala/BabyLemmatizer\n')
                f.write('# global.columns = ' + ' '.join(FIELDS) + '\n')
            for comments, sentence in self.data:
                if comments:
                    for comment in comments:
                        f.write(comment + '\n')
                for word in sentence:
                    f.write('\t'.join(word) + '\n')
                f.write('\n')


    def get_word_freqs(self, field):
        """ Yields word frequencies """
        for k, v in sorted(self.freqs[field].items(),
                           key=lambda item: item[1], reverse=True):
            yield (v, round(100*v/self.word_count, 3), k)

            
    def get_contents(self, *fields):
        """ Yield given fields from data, e.g. xpos tags for each word
        :param *fields        Fields to be fetched
        :type *fields         *str """
        
        for _, sentences in self.data:
            for sent in self._iterate_fields(sentences, *fields):
                yield sent

                    
    def get_contexts(self, *fields, size=1):
        """ Fetch surrounding contexts of any fields
        :param *fields        Fields to be fetched
        :param size           Context size (how many adjacent)
        :type *fields          *str
        :type size            int """
        
        print(f'> Fetching contexts for \"{"|".join(fields)}\"')
        if len(fields) > 1:
            start = tuple([SOU] * len(fields))
            end = tuple([EOU] * len(fields))
        else:
            start, end = SOU, EOU

        """ Set window size and collect buffered tag sequence """
        window = (size * 2) + 1
        for _, sentences in self.data:
            sequence = [start] * size
            for unit in self._iterate_fields(sentences, *fields):
                sequence.append(unit)
            sequence.extend([end] * size)

            """ Yield window-length context sequences """
            for i, seq in enumerate(sequence):
                seq = sequence[i:window+i]
                if len(seq) != window:
                    continue
                if seq[size] not in UNIT_MARKERS:
                    yield seq

    def conditional_update_value(self, mappings, fields):

        self.e = 0
        self.subs = 0
        self.score = 0

        def update(sent):
            key = tuple(sent[FIELDS[field]] for field in fields)
            substitutions = mappings.get(key, None)
            if substitutions is not None:
                for index, sub in substitutions.items():
                    if isinstance(index, int):
                        if sent[index] != sub:
                            sent[index] = sub
                            self.subs += 1
                            
                sent[FIELDS['score']] = str(float(sent[FIELDS['score']]) + substitutions['score'])
                self.score += substitutions['score']
            self.e += 1
            return sent
        
        self.data = [(comments, [update(sent) for sent in sents]) for
                     comments, sents in self.data]

        print(f'  + Step score: {round(self.score / self.e, 2)} '\
              f'Substitutions: {self.subs} '\
              f'({round(100*self.subs / self.e, 2)}%)')
                
        
    def update_value(self, field, values):
        print(f'> Updating field "{field}"')
        ## TODO: fix and add multi-field update
        def update(sent):
            vals = next(values)
            if isinstance(vals, (tuple, list)):
                vals = '|'.join(vals)
            sent[FIELDS[field]] = str(vals)
            #else:
            #    vals = next(values)
            #    for field, vals in zip(fields, zip(*vals)):
            #        if isinstance(vals, (tuple, list)):
            #            vals = '|'.join(vals)
            #        sent[FIELDS[field]] = str(vals)
                
            return sent

        self.data = [(comments, [update(sent) for sent in sents]) for comments, sents in self.data]


    def force_value(self, field, value):
        print(f'> Removing field "{field}"')
        def update(sent):
            sent[FIELDS[field]] = value
            return sent
        
        self.data = [(comments, [update(sent) for sent in sents]) for comments, sents in self.data]
        
if __name__ == "__main__":
    #x = ConlluPlus('input/example.conllu')
    #contexts = x.get_contexts('form', 'xpos', size=1)
    #x.update_value('formctx', 'xposctx',  values=contexts)

    #for l in x.get_contents():
    #    print('NEW\t', l)

    y = ConlluPlus('input/example_nn.conllu')
            
    contexts = y.get_contexts('xpos', size=2)

    for l in contexts:
        print('NEW\t', l)

                        