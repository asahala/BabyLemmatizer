import os
import re
from collections import defaultdict
from metadata import PERIODS, WORDLANGS, TEXTLANGS, LANG_TO_PERIOD, POSMAP

""" ==========================================================
BabyLemmatizer 2.0

https://github.com/asahala/BabyLemmatizer

An ugly script for creating data sets from VRT files

========================================================== """

oracc_2019 = (os.path.join('oracc2019', x) for x in os.listdir('oracc2019'))
oracc_2023 = (os.path.join('oracc2023', x) for x in os.listdir('oracc2023'))

xlit, lemma, pos_oracc, xscript, eng, eng_s, lang, cdli, period, genre, subgenre, language = 0,1,2,3,4,5,6,7,8,9,10,11

postags = set()

def parse(oracc):
    i = 0
    for file in oracc:
        path, fn = os.path.split(file)
        print(file)
        with open(file, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                i += 1
                if line.startswith('<text'):
                    line = line.replace('', '')
                    line = line.replace('=""', '="_"')
                    if path == 'oracc2019':
                        cdli = re.sub('.* cdlinumber="(.+?)".*', r'\1', line)
                        period = re.sub('.* period="(.+?)".*', r'\1', line)
                        genre = re.sub('.* genre="(.+?)".*', r'\1', line)
                        language = re.sub('.* language="(.+?)".*', r'\1', line)
                        subgenre = re.sub('.* subgenre="(.+?)".*', r'\1', line)
                    elif path == 'oracc2023':
                        cdli = re.sub('.* cdlinumber="(.+?)".*', r'\1', line)
                        period = re.sub('.* period="(.+?)".*', r'\1', line)
                        genre = re.sub('.* genre="(.+?)".*', r'\1', line)
                        language = re.sub('.* language="(.+?)".*', r'\1', line)
                        subgenre = re.sub('.* subgenre="(.+?)".*', r'\1', line)
                        
                elif not line.startswith('<'):
                    if path == 'oracc2019':
                        data = line.split('\t')
                        xlit, lemma, eng, eng_s, xscript, pos, pos_oracc, x, lang, id_ = data
                        pos_oracc = pos_oracc.split(' ')[0]
                    elif path == 'oracc2023':
                        data = line.split('\t')

                        xlit, lemma, eng, eng_s, xscript, pos, pos_oracc, x, lang, nnorm, x, id_ = data
                        pos_oracc = pos_oracc.split(' ')[0]
                        
                    _lang = WORDLANGS[lang]
                    _period = PERIODS[period]
                    _language = TEXTLANGS[language]

                    #postags.add(pos_oracc)

                    pos_oracc = POSMAP.get(pos_oracc, pos_oracc)

                    """ Get word lang from text lang if not available """
                    if _lang == '_':
                        textlangs = _language.split('|')
                        if len(textlangs) == 1:
                            _lang = _language

                    """ Guess period by language """
                    if _period == '_':
                        _period = LANG_TO_PERIOD.get(lang, '_')
                            
                    yield '\t'.join(x.replace('&amp;', '&') for x in [xlit,
                                     lemma,
                                     pos_oracc,
                                     xscript,
                                     eng,
                                     eng_s,
                                     _lang,
                                     cdli,
                                     _period.lower(),
                                     genre,
                                     subgenre,
                                     _language]
                                    )

                if line.startswith('</sentence>'):
                    yield ''
                    
def make_txt():        
    with open('oracc2023.txt', 'w', encoding='utf-8') as f:
        for line in parse(oracc_2023):
            f.write(line + '\n')

    with open('oracc2019.txt', 'w', encoding='utf-8') as f:
        for line in parse(oracc_2019):
            f.write(line + '\n')
        
def write_file(name, content):
    with open(os.path.join('datasets', name), 'w', encoding='utf-8') as f:
        for line in content:
            f.write(line + '\n')



def filter_texts(textfiles, condition):
    for textfile in textfiles:
        with open(textfile, 'r', encoding='utf-8') as file:
            last = False
            for i, line in enumerate(file):
                line = line[0:-1]
                if line:
                    data = line.split('\t')
                    if condition(data):
                        last = True
                        yield line
                else:
                    if last:
                        yield ''
                    last = False


def is_sumerian(data):
    return 'sumerian' in data[lang]

def is_babylonian(data):
    if re.match('.*(akk|bab).+', data[lang]) and data[period] == 'first millennium':
        return True
    return False

def is_neoassyrian(data):
    if re.match('.*(ass|standard).+', data[lang]) and data[period] == 'first millennium':
        return True
    if re.match('.*(neo-assyrian).+', data[language]) and re.match('.*(ass|akk|bab).+', data[lang]):
        return True
    return False

def is_hurrian(data):
    return 'hurrian' in data[lang]

def is_urartian(data):
    return 'urartian' in data[lang]
  
      
def rawtext_to_conllu(filename):

    head = {1: '0'}
    deprel = {1: 'root'}
    print(filename)
    outfile = filename.replace('.txt', '.conllu')
    with open(filename, 'r', encoding='utf-8') as txt,\
         open(outfile, 'w', encoding='utf-8') as out:
        unit = []
        lemmata = set()
        tags = set()
        for line in txt:
            line = line[0:-1]
            if line:
                data = line.split('\t')
                unit.append(data)
                lemmata.add(data[lemma])
                lemmata.add(data[pos_oracc])
            else:
                """ check that the chunk has lemmatization """
                if lemmata == tags:
                   pass
                elif lemmata == set('*'):
                    pass
                else:
                    for e, u in enumerate(unit, start=1):
                        u[eng] = re.sub('=', '═', u[eng])
                        u[xscript] = re.sub('=', '-', u[xscript])

                        pairs = (('Translation', u[eng]),
                                 ('Normalization', u[xscript]))
                        items = [f'{x}={y}' for x, y in pairs if y != '_']

                        misc = '|'.join(items)

                        if not misc:
                            misc = '_'

                        conlluline = (str(e),
                                      u[xlit],
                                      u[lemma],
                                      u[pos_oracc],
                                      u[pos_oracc],
                                      '_',
                                      head.get(e, '1'),
                                      deprel.get(e, 'child'),
                                      '_',
                                      misc)
                        out.write('\t'.join(conlluline) + '\n')
                    out.write('\n')
                    
                lemmata = set()
                unit = []


def n_fold_split(n, data):

    """ Split dataset into n-fold train/test sets

    :param n          number of splits
    :param data       dataset
    :type n           int
    :type data        list of es text objects

    """
       
    train_data = defaultdict(list)
    test_data = defaultdict(list)
    dev_data = defaultdict(list)

    if n == 1:
        return {0: data}, {0: data}, {0: data}
   
    for e, entry in enumerate(data):
        for split in range(0, n):

            devsplit = split+1
            if devsplit == n:
                devsplit = 0
                
            if e % n == split:
                test_data[split].append(entry)
            elif e % n == devsplit:
                dev_data[split].append(entry)
            else:
                train_data[split].append(entry)

    return train_data, test_data, dev_data


def make_training_sets(file):
    set_units = set()
    units = []
    this_unit = []
    removed = 0
    with open(file, 'r', encoding='utf-8') as source:
        for line in source.read().splitlines():
            this_unit.append(line)
            if not line:
                """ Remove duplicates """
                if len(this_unit) > 12 and tuple(this_unit) in set_units:
                    
                    removed += 1
                    print(removed, len(this_unit))
                    this_unit = []
                    continue
                
                units.append(tuple(this_unit))
                set_units.add(tuple(this_unit))
                this_unit = []

    train, dev, test = n_fold_split(10, units)

    path, fn = os.path.split(file)

    fn = fn.split('.')[0]
    
    for n in range(0,10):
        number = str(n)
        prefix = fn + number

        for suffix, dataset in (('train', train), ('dev', dev), ('test', test)):
            print(suffix, len(dataset[n]))
            with open(f'{prefix}-{suffix}.conllu', 'w', encoding='utf-8') as out:
                for unit in dataset[n]:
                    for line in unit:
                        out.write(line + '\n')
        
    
#make_txt()
                
#write_file('sumerian.txt', filter_texts(('oracc2019.txt', 'oracc2023.txt'), is_sumerian))
#write_file('babylonian_1st.txt', filter_texts(('oracc2019.txt', 'oracc2023.txt'), is_babylonian))
#write_file('neoassyrian.txt', filter_texts(('oracc2019.txt', 'oracc2023.txt'), is_neoassyrian))
#write_file('hurrian.txt', filter_texts(('oracc2019.txt', 'oracc2023.txt'), is_hurrian))
#write_file('urartian.txt', filter_texts(('oracc2019.txt', 'oracc2023.txt'), is_urartian))
            
#rawtext_to_conllu('datasets/urartian.txt')
#rawtext_to_conllu('datasets/sumerian.txt')
#rawtext_to_conllu('datasets/neoassyrian.txt')
#rawtext_to_conllu('datasets/babylonian_1st.txt')

#make_training_sets('datasets/neo-babylonian.conllu')


