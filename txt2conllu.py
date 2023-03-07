import os
from argparse import ArgumentParser
import preprocessing

"""===========================================================
Rawtext -> CoNLL-U+ for BabyLemmatizer 2

asahala 2023
https://github.com/asahala

University of Helsinki
   Origins of Emesal Project
   Centre of Excellence for Ancient Near-Eastern Empires

==========================================================="""

def normalize(xlit):
    xlit = xlit.replace('sz', 'š')
    xlit = xlit.replace('SZ', 'Š')
    xlit = xlit.replace('s,', 'ṣ')
    xlit = xlit.replace('t,', 'ṭ')
    xlit = preprocessing.lowercase_determinatives(xlit)
    xlit = preprocessing.unify_h(xlit)
    xlit = preprocessing.subscribe_indices(xlit)
    return xlit

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
            if line.startswith('#'):
                o.write(line + '\n')
                continue
            for word in line.strip().split(' '):
                hh = head.get(i, '1')
                rr = deprel.get(i, 'child')
                o.write(f'{i}\t{normalize(word)}\t_\t_\t_\t_\t{hh}\t{rr}\t_\t_\n')
                i += 1
            o.write('\n')

    print(f'> File converted to CoNLL-U+ and saved as {output}')

if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument('--filename', type=str)
    args = ap.parse_args()

    if args.filename:
        txt = args.filename
        fn, ext = os.path.splitext(args.filename)
        conllu = fn + '.conllu'

        upl_to_conllu(txt, conllu)
        
