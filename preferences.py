import os

""" Virtual environment path that contains all requirements for OpenNMT """
python_path = '/projappl/clarin/onmt/OpenNMT/bin/'

""" OpenNMT-Py path, i.e. where the OpenNMT binaries are """
onmt_path = './OpenNMT-py/onmt/bin/'


class Paths:

    """ Container for crucial paths """
    conllu = 'conllu'
    models = 'models'
    
    
if __name__ == "__main__":
    os.system(f'{python_path}python {onmt_path}train.py -h')

