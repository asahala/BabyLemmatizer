import os
from preferences import python_path, onmt_path
import conllutools as ct

""" ===========================================================
API for calling OpenNMT and performing intermediate steps for
BabyLemmatizer 2.0

asahala 2023
https://github.com/asahala

University of Helsinki
   Origins of Emesal Project
   Centre of Excellence for Ancient Near-Eastern Empires

=========================================================== """

def _rename_model(model_name, type_):
    
    def get_step(filename):
        return int(''.join(c for c in filename if c.isdigit()))
        
    path = os.path.join('models', model_name, type_)
    step = sorted(get_step(x) for x in os.listdir(path) if x.endswith('.pt'))[-1]

    old_name = f'model_step_{step}.pt'
    new_name = 'model.pt'
    os.rename(os.path.join(path, old_name), os.path.join(path, new_name))

    
def run_tagger(input_file, model_name, output_file): 
    command = f"{python_path}python {onmt_path}translate.py -model"\
        f" {model_name} -src {input_file} -output {output_file} -gpu 0 -min_length 1"
    os.system(command)
    _rename_model(model_name, 'tagger')
    

def run_lemmatizer(input_file, model_name, output_file):
    command = f"{python_path}python {onmt_path}translate.py -model"\
              f" {model_name} -src {input_file} -output {output_file} -gpu 0 -min_length 1"
    os.system(command)
    _rename_model(model_name, 'lemmatizer')


def merge_tags(tagged_file, lemma_input, output_file):
    """ This function merges Tagger output with lemmatizer test data
    to create input for lemmatizer evaluation """

    def filter_pos(string):
        xlit = string.split(' PREV')[0]
        return xlit
    
    with open(tagged_file, 'r', encoding='utf-8') as t_file,\
         open(lemma_input, 'r', encoding='utf-8') as l_file,\
         open(output_file, 'w', encoding='utf-8') as o_file:

        lemmas = (filter_pos(x) for x in l_file.read().splitlines())
        tag_segments = []
        stack = [ct.EOU[0]]
        for tag in t_file.read().splitlines():
            stack.append(tag)
            if len(stack) == 3:
                tag_segments.append('PREV={} UPOS={} NEXT={}'.format(*stack))
                stack.pop(0)

        tag_segments.append('PREV={} UPOS={} NEXT={}'.format(*stack, ct.EOU[0]))
        
        for lemma, pos in zip(lemmas, tag_segments):
            if lemma == ct.EOU[0]:
                o_file.write(lemma + '\n')
            else:
                o_file.write(f'{lemma} {pos}\n')


def merge_to_final(tags, lemmas, output):
    """ Merges tags and lemmata into a single output """
    with open(tags, 'r', encoding='utf-8') as t_file,\
         open(lemmas, 'r', encoding='utf-8') as l_file,\
         open(output, 'w', encoding='utf-8') as o_file:

        combined = zip(l_file.read().splitlines(),
                       t_file.read().splitlines())

        for lemma, pos in combined:
            o_file.write(f'{lemma}\t{pos}\n')

        o_file.write('\n')


def file_to_set(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return set(x.split('\t')[0] for x in f.read().splitlines())


def assign_confidence_scores(model):

    def is_logogram(xlit):
        return xlit.lower() != xlit
            
    results = ct.read_conllu(
        f'./models/{model}/eval/output_final.conllu')
    oov_lem = f'./models/{model}/override/test-types-oov.lem'
    oov_xlit = f'./models/{model}/override/test-types-oov.xlit'
    output = f'./models/{model}/eval/output_final.conllu2'

    oov_lem = file_to_set(oov_lem)
    oov_xlit = file_to_set(oov_xlit)

    with open(output, 'w', encoding='utf-8') as f:
        for line in results:
            if line.startswith('#'):
                f.write(line + '\n')
            if not line:
                f.write('\n')
            else:
                data = line.split('\t')

                conf_score = 3.0
                
                if f'{data[2]} {data[3]}' in oov_lem:
                    conf_score = 2.0
                if data[1] in oov_xlit:
                    if is_logogram(data[1]):
                        conf_score = 0.0
                    else:
                        conf_score = 1.0

                data[-1] = str(conf_score)
                f.write('\t'.join(data) + '\n')
    
