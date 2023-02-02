import os
from preferences import python_path, onmt_path
from conllutools import EOU

def run_tagger(input_file, model_name, output_file): 
    command = f"{python_path}python {onmt_path}translate.py -model"\
        f" {model_name} -src {input_file} -output {output_file} -gpu 0 -min_length 1"
    os.system(command)


def run_lemmatizer(input_file, model_name, output_file):
    command = f"{python_path}python {onmt_path}translate.py -model"\
              f" {model_name} -src {input_file} -output {output_file} -gpu 0 -min_length 1"
    os.system(command)


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
        #tags = (f'UPOS={x}' for x in t_file.read().splitlines())

        tag_segments = []

        stack = [EOU[0]]
        for tag in t_file.read().splitlines():
            stack.append(tag)
            if len(stack) == 3:
                #if stack[1] != '<EOU>':
                tag_segments.append('PREV={} UPOS={} NEXT={}'.format(*stack))
                stack.pop(0)

        tag_segments.append('PREV={} UPOS={} NEXT=<EOU>'.format(*stack))
        
        for lemma, pos in zip(lemmas, tag_segments):
            if lemma == EOU[0]:
                o_file.write(lemma + '\n')
            else:
                o_file.write(f'{lemma} {pos}\n')


def merge_to_final(tags, lemmas, output):
    """ General file merger """
    with open(tags, 'r', encoding='utf-8') as t_file,\
         open(lemmas, 'r', encoding='utf-8') as l_file,\
         open(output, 'w', encoding='utf-8') as o_file:

        combined = zip(l_file.read().splitlines(),
                       t_file.read().splitlines())

        for lemma, pos in combined:
            o_file.write(f'{lemma}\t{pos}\n')

        o_file.write('\n')
