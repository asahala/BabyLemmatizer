import time
import re
import os
from collections import defaultdict
import preprocessing as PP
import cuneiformtools.tests as tests

""" ============================================================

CoNLL-U+ file processor for BabyLemmatizer 2
asahala 2023
github.com/asahala/BabyLemmatizer


FORMAT DESCRIPTION:

CoNLL-U+ is the standard input/outpu format for BabyLemmatizer 2.
Currently direct lemmatization of JSON or ATF is not supported.

Fields in BabyLemmatizer 2 CoNLL-U+

   Standard fields:

   `id`        Word's position in the unit (line/text/sentence)
   `form`      Transliteration
   `lemma`     Lemma
   `upos`      UD POS-tag if available
   `xpos`      Oracc POS tag
   `feats`     Morphological features, now always _
   `head`      Dependency stuff, always 0 or 1
   `deprel`    Dependency stuff, always root or child
   `deps`      More stuff, always _
   `misc`      Arbitrary information

   Additional fields:

   `eng`       English translation (i.e. dictionary meaning)
   `norm`      Phonological/ other normalization (transcription)
   `lang`      Word language
   `formctx`   Context of the word as transliteration, i.e. form
   `xposctx`   Context of the word as XPOS tag
   `score`     Confidence score
   `lock`      Write-protection for the field

   Formal info:

   None of the fields are allowed to contain tabs.
   Only fields `eng` and `misc` are allowed to contain space.

   `id` must be a number ≥1, multi-word lines like 2-4 are not
   allowed. If you have compound words, join them with ampersand
   e.g. word&&word and their xpos-tags TAG&&TAG. Or just add
   these for separate lines.

============================================================ """


""" GLOBAL VARS """
# CoNLL-U+ field names; never change this order
FIELD_NAMES = ('id', 'form', 'lemma', 'upos', 'xpos', 'feats',
               'head', 'deprel', 'deps', 'misc', 'eng', 'norm',
               'lang', 'formctx', 'xposctx', 'score', 'lock')

FIELDS = {name: index for index, name in enumerate(FIELD_NAMES)}

ID, FORM, LEMMA, UPOS, XPOS, FEATS,\
    HEAD, DEPREL, DEPS, MISC, ENG, NORM,\
    LANG, FORMCTX, XPOSCTX, SCORE, LOCK = FIELDS.values()

LAST_FIELD = max(FIELDS.values())

# CoNLL-U+ unit boundaries
SOU = '<SOU>'
EOU = '<EOU>'
UNIT_MARKERS = frozenset((SOU, EOU))

# Lemmadict field separators
LDICT_SEP = '│'        # Standard entry
LDICT_SEP_MULTI = '╬'  # Ambiguous entry

# TODO: Add verbose option

""" Utility functions """

def sort_dict(dictionary):
    """ Sort dictionary by value """
    for k, v in sorted(dictionary.items(),
                       key=lambda item: item[1],
                       reverse=True):
        yield k, v
        

def merge_backup(backup_file, pp_file):
    with open(pp_file, 'r', encoding='utf-8') as f:
        pp = f.read().splitlines()
    
    with open(backup_file, 'r', encoding='utf-8') as f,\
         open(pp_file, 'w', encoding='utf-8') as f_o:
        for line in f.read().splitlines():
            pp_line = pp.pop(0)
            if not line:
                f_o.write(line + '\n')
            elif line.startswith('#'):
                f_o.write(line + '\n')
            else:
                if line.split('\t')[-1] != '_':
                    f_o.write(line + '\n')
                else:
                    f_o.write(line + '\n')
    
                        
class LemmaDict:

    """ Class for constructing and writing lemma
    dictionaries for manual post-correction """
    
    def __init__(self):
        self.data = {}
        self.counts = defaultdict(int)

        
    def add_entry(self, form, lemma, xpos):
        
        if form not in self.counts:
            self.data[form] = defaultdict(int)

        self.data[form][(lemma, xpos)] += 1        
        self.counts[form] += 1

        
    def write_file(self, score, filename):
        filename, extension = os.path.splitext(filename)
        o_file = filename + '_' + score.replace('.', '') + '.tsv'
        
        with open(o_file, 'w', encoding='utf-8') as f:
            f.write('# {frq: <5} │ {frm: <37} │ {lem: <22} │ {pos}\n'\
                    .format(frq='FREQ', frm='FORM',
                            lem='LEMMA', pos='XPOS'))
            f.write('#' + '─'*79 + '\n')
            for form, _ in sort_dict(self.counts):
                sep = LDICT_SEP
                if len(self.data[form]) > 1:
                    sep = LDICT_SEP_MULTI
                for lemmaxpos, count in sort_dict(self.data[form]):
                    lemma, xpos = lemmaxpos
                    f.write(f'# {count : <5} {sep} {form : <37} '
                            f'{sep} {lemma : <22} {sep} {xpos}\n')

        print(f'> Wrote low-confidence lemmatizations to {o_file}')


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

        if filename is None:
            pass
        elif filename.endswith('.conllu'):
            self.read_file(filename)
        elif filename.endswith('.tsv'):
            self.read_corrections(filename)
        #self.word_count = sum(len(unit) for _, unit in self.data)


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
        if line[FIELDS['lemma']] == '_' and not line[FIELDS['form']][0].isdigit():
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


    def read_corrections(self, filename):
        """ Read corrected lemma files into CoNLL-U+ 

        :param filename        filename
        :type filename         str / path

        If this method is called repeatedly, it will
        concatenate all the files. """   

        print(f'> Reading corrections from {filename}')
        
        with open(filename, 'r', encoding='utf-8') as f:
            for e, line in enumerate(f):

                if line.startswith('#'):
                    continue
                
                line = line.rstrip()\
                           .replace(' ', '')\
                           .replace(LDICT_SEP_MULTI, LDICT_SEP)\
                           .split(LDICT_SEP)
                
                if len(line) != 4:
                    print(f'ärör {e}')
                    sys.exit(0)

                _, form, lemma, xpos = line
                
                base = list('_' * (1+ len(FIELDS)))

                base[ID] = '1'
                base[FORM] = form
                base[LEMMA] = lemma
                base[XPOS] = xpos
                base[HEAD] = '0'
                base[DEPREL] = 'root'
                
                self.data.append(([''], [base]))

        self.word_count = sum(len(unit) for _, unit in self.data)
            

    def read_file(self, filename):
        """ Reads and parses a CoNLL-U+ file. Forces
        additional fields for extra information 

        :param filename        filename
        :type filename         str / path  

        If this method is called repeatedly, it will
        concatenate all the CoNLL-U+ files. """

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

                    """ Fix empty elements """
                    if '' in set(line):
                        print(f'> ERROR: Empty field at line {e} -> '\
                              'replaced with _')
                        line = [x if x != '' else '_' for x in line]
                        
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
            print('\n')

        self.word_count = sum(len(unit) for _, unit in self.data)

            
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
            if sent[LOCK] != '_':
                self.e += 1
                return sent
            
            key = tuple(sent[FIELDS[field]] for field in fields)
            substitutions = mappings.get(key, None)
            if substitutions is not None:
                for index, sub in substitutions.items():
                    if isinstance(index, int):
                        if sent[index] != sub:
                            sent[index] = sub
                            self.subs += 1
                            
                sent[FIELDS['score']] = str(float(
                    sent[FIELDS['score']]) + substitutions['score'])
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
            if sent[LOCK] != '_':
                return sent
            
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

        self.data = [(comments, [update(sent) for sent in sents])
                     for comments, sents in self.data]


    def force_value(self, field, value):
        print(f'> Removing field "{field}"')
        def update(sent):
            if sent[LOCK] != '_':
                return sent
            sent[FIELDS[field]] = value
            return sent
        
        self.data = [(comments, [update(sent) for sent in sents])
                     for comments, sents in self.data]


    def remove_unannotated(self, sent):
        pass
    

    def normalize(self, is_traindata=False):
        """ Run all normalizations for lemmatization and 
        transliteration. 

        :param is_trainingdata     This data is used for training
        :type is_trainingdata      bool 

        """

        ## TODO: laita mahdollisuus korjata virheitä
        ## esim. poistaa xlit jos ei lemmattu
        
        print(f'> Normalizing CoNLL-U')
        def update(sent):
            if sent[LOCK] != '_':
                return sent
            xlit = sent[FORM]
            lemma = sent[LEMMA]
            xlit = PP.lowercase_determinatives(xlit)
            xlit = PP.subscribe_indices(xlit)
            xlit = PP.unify_h(xlit)
            xlit = PP.remove_brackets(xlit)
            lemma = PP.unify_h(lemma)
            if not xlit:
                xlit = '_'
            if not lemma:
                lemma = '_'

            #if is_traindata:
            #    sent = self.remove_unannotated

            sent[FORM] = xlit
            sent[LEMMA] = lemma
            return sent

        self.data = [(comments, [update(sent) for sent in sents])
                     for comments, sents in self.data]


    def override_form(self, dictionary):
        """ Overides any annotation given to a form 

        :param dictionary      override dictionary
        :type dictionary       dict

        {form: {lemma: x, xpos: y}, ...} """

        ## TODO: Update also POS-contexts, now old context remains
        
        def update(sent):
            if sent[LOCK] != '_':
                return sent
            values = dictionary.get(sent[FORM], None)
            if values is None:
                return sent
            
            for k, v in values.items():
                sent[FIELDS[k]] = v
            sent[SCORE] = '4.0'
            return sent

        self.data = [(comments, [update(sent) for sent in sents])
                     for comments, sents in self.data]
           
        
    def make_lemmalists(self):
        """ Extract all low-confidence lemmatizations from
        the file and write them into correction glossaries 
        aka lemmadicts. """
        
        lemmadict = defaultdict(LemmaDict)
    
        for comments, unit in self.data:
            for form, lemma, xpos, score in self._iterate_fields(
                    unit, 'form', 'lemma', 'xpos', 'score'):
                if score == '_':
                    continue
                if float(score) <= 2.0:
                    lemmadict[score].add_entry(form, lemma, xpos)

        for score, ldict in lemmadict.items():
            ldict.write_file(score, self.filename)


    def unlemmatize(self, numbers=True):
        """ Remove lemmatization from numerals """

        if numbers:
            print('> Removing lemmatizations of numbers')
        
        self.nums_removed = 0
        self.lacunae_removed = 0
        def update(sent):
            if sent[LOCK] != '_':
                return sent

            field_type = tests.is_numeral(sent[FORM])
            if field_type:
                self.nums_removed += 1
                sent[LEMMA] = '_'
                sent[XPOS] = 'n'
                sent[MISC] = field_type
                sent[SCORE] = '_'

            lacuna_type = tests.is_lacuna(sent[FORM])
            if lacuna_type:
                self.lacunae_removed += 1
                sent[LEMMA] = '_'
                sent[XPOS] = 'u'
                sent[MISC] = lacuna_type
                sent[SCORE] = '_'
                
            return sent
            
        self.data = [(comments, [update(sent) for sent in sents])
                     for comments, sents in self.data]

        if self.nums_removed:
            print(f'  + {self.nums_removed} numbers flattened')
        if self.lacunae_removed:
            print(f'  + {self.lacunae_removed} lacunae flattened')


if __name__ == "__main__":
    #y = ConlluPlus('achemenet/achemenet-murashu.conllu', validate=False)
    #contexts = x.get_contexts('form', 'xpos', size=1)
    #x.update_value('formctx', 'xposctx',  values=contexts)

    #for l in x.get_contents():
    #    print('NEW\t', l)

    y = ConlluPlus('everling/EverlingNB_pp.conllu', validate=False)
    #y.read_corrections('input/test_pp_10.tsv')
    #for x in y.get_contents():
    #    print(x)
    #merge_backup('demo/backup.conllu', 'demo/enuma_pp.conllu')                   
    x = y.get_contexts('form')
    print(x)
