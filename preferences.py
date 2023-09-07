import os
import sys

""" BabyLemmatizer 2 Preferences ==================================

  asahala 2023
  github.com/asahala/BabyLemmatizer

=============================================================== """

version_history =\
    "1.0    2022-05-01    TurkuNLP dependent version.\n"\
    "2.0    2023-03-08    Moved to OpenNMT from TurkuNLP.\n"\
    "2.1    2023-09-05    Model versioning --tokenizer.\n"

__version__ = '2.1'

""" Virtual environment path that contains all requirements for OpenNMT """
python_path = '/projappl/clarin/onmt/OpenNMT/bin/'

""" OpenNMT-Py path, i.e. where the OpenNMT binaries are """
onmt_path = './OpenNMT-py/onmt/bin/'


class Paths:

    """ Container for crucial paths """
    conllu = 'conllu'
    models = 'models'
    override = 'override'
    

class Tokenizer:

    """ This class controls tokenizer behavior 

    0 = Logo-syllabic (Akkadian, Urartian, Hittite, Elamite)
    1 = Sumerian
    2 = Character sequence (Greek, Latin, Persian, Ugaritic etc.)  

    This info is saved in to model config.txt"""
    
    setting = 0

    def read(prefix):
        if not os.path.isfile(os.path.join(Paths.models, prefix, 'config.yaml')):
            print('> Your model was trained with an old version of BabyLemmatizer.')
            print('> Using Tokenizer setting 0. Rebuild model using --tokenizer.')
            Tokenizer.setting = 0
        else:
            with open(os.path.join(Paths.models, prefix, 'config.yaml')) as f:
                for l in f.read().splitlines():
                    l = l.replace(' ', '')
                    if l.startswith('tokenizer'):
                        val = int(l.split(':')[-1])
                        Tokenizer.setting = val
                        
        print(f'> Using tokenizer {Tokenizer.setting}')
        

    
if __name__ == "__main__":
    os.system(f'{python_path}python {onmt_path}train.py -h')

