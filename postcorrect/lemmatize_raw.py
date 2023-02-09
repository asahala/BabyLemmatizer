import re
#import postcorrect.vrt_to_conllu as vrt2conllu
import postcorrect.minimize as minimize
import postcorrect.unminimize as unminimize
import postcorrect.baseline as baseline
import postcorrect.evaluate as evaluate
import postcorrect.disambiguator as disambiguator
import postcorrect.postcorrect as postcorrect
import postcorrect.logogram_analyzer as LA
from collections import defaultdict
import json

## Script for lemmatizing Achemenet

def choose(o, f):
    if o.startswith('#') and not f:
        return o
    return f
    
def override(item, glo):
    """ This is specific for achemenet: use glossary files provided by
    Tero Alstola to override OOV lemmatization """
    if item.startswith('#'):
        return item
    if not item:
        return item
    else:
        d = item.split('\t')
        xlit, lem, pos = d[1], d[2], d[3]
        if 'x' in xlit or '...' in xlit:
            return '\t'.join([d[0], xlit, '_', 'u'] + d[4:-1] + ['lac'])
        elif xlit[0].isdigit():
            return '\t'.join([d[0], xlit, '_', 'n'] + d[4:-1] + ['num'])
                
        if item.endswith(('0.0', '1.0')):
            d = item.split('\t')
            xlit = d[1]
            g_lem, g_pos = glo.get(xlit, (None, None))
            p_lem, p_pos = d[2], d[3]

            if g_lem is not None:
                d[2] = g_lem
                d[3] = g_pos
                d[-1] = '2.5'
            return '\t'.join(d)

        d = item.split('\t')
        if d[3] == 'u' and d[1].startswith('{m}'):
            d[3] = 'PN'
            d[-1] = 'lac'
            return '\t'.join(d)
        
        else:
            return item

def lemmatize_unseen(lemmatizer_output,
                     master,
                     override_lexicon=None,
                     master_glo=None):

    """ :param lemmatizer_output   output from neural net
        :param master              master dictionary """

    """ Make temporary xlit file and remove comments temporarily """
    xlits = []
    with open(lemmatizer_output, 'r', encoding='utf-8') as f:
        for x in f.read().splitlines():
            if x and not x.startswith('#'):
                xlit = x.split('\t')[1]
            else:
                xlit = ''
            xlits.append(xlit)

    with open('tmp.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(xlits))
        
    xlit_file = 'tmp.txt'

    print(master)
    unamb, lemmadict = unminimize.get_unamb2(master,
                                             threshold=0.4)
    output = unminimize.fill_unamb(lemmatizer_output, xlit_file,
                                   unamb, lemmadict)

    """ Postcorrections """
    output = postcorrect.process(output)
    
    output = disambiguator.add_context(list(output), 'pos-map.json')

    """ Add contexts and disambiguate """
    traindata = disambiguator.readfile(master)
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

    """ Reinsert comments """
    with open(lemmatizer_output, 'r', encoding='utf-8') as f:
        original = f.read().splitlines()
        output = [choose(orig, final) for orig, final\
                  in zip(original, output)]

    if master_glo is not None:
        with open(master_glo, 'r', encoding='utf-8') as json_data:
            master_glossary = json.load(json_data)


        """ Override with Glossary data """
        output = [override(l, master_glossary) for l in output]

    """ Read secondary override """
    if override_lexicon is not None:
        olex = {}
        with open(override_lexicon, 'r', encoding='utf-8') as f:
            for item in f.read().splitlines():
                xlit, lem, pos = item.split('\t')
                olex[xlit] = (lem, pos)

        output = [override(l, olex) for l in output]

    '''
    """ Get confidence scores """
    scores = defaultdict(int)
    oov00 = defaultdict(int)
    oov00preds = defaultdict(set)
    for o in output:
        if o and not o.startswith('#'):
            d = o.split('\t')
            conf = d[-1]
            xlit = d[1]
            lem = d[2]
            pos = d[3]

            if conf in ('0.0'):
                oov00[xlit] += 1
                oov00preds[xlit].add(lem+'['+pos+']')
            scores[conf] += 1

    for k, v in scores.items():
        print(k, v)
    '''
    #pot_errs = []
    #for k, v in sorted(oov00.items(), key=lambda item: item[1], reverse=True):
    #    pot_errs.append(str(v) + '\t' + k + '\t' + ' | '.join(oov00preds[k]))

    #with open('../input/oov00.txt', 'w', encoding='utf-8') as f:
    #    f.write('\n'.join(pot_errs))
        
    """ Write to file """
    unminimize.write_conllu(lemmatizer_output+'.final', output)


#lemmatize_unseen('../input/murashu.conllu',
#                 '../models/babylonian/baby-master-for-achemenet-dash.conllu',
#                 '../models/babylonian/neobab-glossary-for-achemenet.json')


#lemmatize_unseen('../input/textesbabmurashu_20210825_lem_output.conllu',
#                 '../models/achemenet/baby-master-for-achemenet-dash.conllu',
#                 '../models/achemenet/override.tsv',
#                 '../models/achemenet/neobab-glossary-for-achemenet.json')


#lemmatize_unseen('../input/textesbabmurashu_20210825_xscript_output.conllu',
#                 '../models/achemenet/transcription-master.conllu')


def lower_determinatives(file):
    """ Lowercase determinatives """
    def read():
        with open(file, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                if not line:
                    yield line
                elif line[0].isdigit():
                    d = line.split('\t')
                    xlit = ''
                    lower = False
                    for c in d[1]:
                        if c == '{':
                            lower = True
                        elif c == '}':
                            lower = False

                        if lower:
                            c = c.lower()

                        xlit += c
                    d[1] = xlit
                    yield '\t'.join(d)
                else:
                    yield line

    def write():
        with open(file + '.lower', 'w', encoding='utf-8') as f:
            for x in read():
                f.write(x + '\n')

    write()

def lower_determinatives_override(file):

    def read():
        with open(file, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                a, lem, pos = line.split('\t')
                A = ''
                lower = False
                for c in a:
                    if c == '{':
                        lower = True
                    elif c == '}':
                        lower = False

                    if lower:
                        c = c.lower()
                    A += c
                L = '\t'.join([A, lem, pos])
                yield L
                    
    def write():
        with open(file + '.lower', 'w', encoding='utf-8') as f:
            for x in read():
                f.write(x + '\n')

    write()
            

def nathan():
    # Nathan's seal inscriptions
    lemmatize_unseen('../input/colbow1995.conllu',
                     '../models/achemenet/baby-master-for-achemenet-dash.conllu',
                     '../models/achemenet/override.tsv',
                     '../models/seals/seal-glossary.json')


def strassmaier():
    #lower_determinatives('../input/strassmaier_20220317_out.conllu')
    #lower_determinatives_override('../models/achemenet/override.tsv')
    #lower_determinatives('../models/achemenet/lblem-train-dash-master-for-achemenet..conllu')
    lemmatize_unseen('../input/strassmaier_202205_out.conllu',
                     '../models/achemenet/lblem-train-dash-master-for-achemenet..conllu.lower',
                     '../models/achemenet/override.tsv.lower',
                     '../models/achemenet/neobab-glossary-for-achemenet.json')

def ct():
    lemmatize_unseen('../input/ct_2022_out.conllu',
                     '../models/achemenet/lblem-train-dash-master-for-achemenet..conllu',
                     '../models/achemenet/override.tsv',
                     '../models/achemenet/neobab-glossary-for-achemenet.json')

def belremanni():
    lemmatize_unseen('../input/belremanni_out.conllu',
                     '../models/achemenet/lblem-train-dash-master-for-achemenet..conllu',
                     '../models/achemenet/override.tsv',
                     '../models/achemenet/neobab-glossary-for-achemenet.json')

def yos():
    lemmatize_unseen('../input/yos_out.conllu',
                     '../models/achemenet_2022/achemenet_lblem.conllu',
                     '../models/achemenet_2022/override.tsv',
                     '../models/achemenet_2022/neobab-glossary-for-achemenet.json')

def jursa():
    lemmatize_unseen('../input/jursa_2022_out.conllu',
                     '../models/achemenet/lblem-train-dash-master-for-achemenet..conllu',
                     '../models/achemenet/override.tsv',
                     '../models/achemenet/neobab-glossary-for-achemenet.json')
def murasu():
    lemmatize_unseen('../input/murashu_out.conllu',
                     '../models/achemenet_2022/achemenet_lblem.conllu',
                     '../models/achemenet_2022/override.tsv',
                     '../models/achemenet_2022/neobab-glossary-for-achemenet.json')

#strassmaier()
#ct()
#belremanni()
#yos()
#jursa()
#murasu()
