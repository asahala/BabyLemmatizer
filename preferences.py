import os

""" BabyLemmatizer 2 Preferences ==================================

  asahala 2023
  github.com/asahala/BabyLemmatizer

=============================================================== """

version_history =\
    "1.0    2022-05-01    TurkuNLP dependent version.\n"\
    "2.0    2023-03-08    Moved to OpenNMT from TurkuNLP.\n"

__version__ = '2.0'

""" Virtual environment path that contains all requirements for OpenNMT """
python_path = '/projappl/clarin/onmt/OpenNMT/bin/'

""" OpenNMT-Py path, i.e. where the OpenNMT binaries are """
onmt_path = './OpenNMT-py/onmt/bin/'


class Paths:

    """ Container for crucial paths """
    conllu = 'conllu'
    models = 'models'
    override = 'override'
    
    
if __name__ == "__main__":
    os.system(f'{python_path}python {onmt_path}train.py -h')

