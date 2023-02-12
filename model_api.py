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
    
def run_tagger(input_file, model_name, output_file, cpu=False):
    gpu = ''
    if not cpu:
        gpu = '-gpu 0'

    command = f"{python_path}python {onmt_path}translate.py -model"\
        f" {model_name} -src {input_file} -output {output_file} {gpu} "\
        "-min_length 1"
    os.system(command)


def run_lemmatizer(input_file, model_name, output_file, cpu=False):
    gpu = ''
    if not cpu:
        gpu = '-gpu 0'
        
    command = f"{python_path}python {onmt_path}translate.py -model"\
              f" {model_name} -src {input_file} "\
              f"-output {output_file} {gpu} -min_length 1"
    os.system(command)


def read_results(filename):
    """ Read OpenNMT output file """
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            
            yield line.replace(' ', '').rstrip()

    
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

        tag_segments.append(
            'PREV={} UPOS={} NEXT={}'.format(*stack, ct.EOU[0]))
        
        for lemma, pos in zip(lemmas, tag_segments):
            if lemma == ct.EOU[0]:
                o_file.write(lemma + '\n')
            else:
                o_file.write(f'{lemma} {pos}\n')


def ___merge_to_final(tags, lemmas, output):
    """ Merges tags and lemmata into a single output """
    with open(tags, 'r', encoding='utf-8') as t_file,\
         open(lemmas, 'r', encoding='utf-8') as l_file,\
         open(output, 'w', encoding='utf-8') as o_file:

        combined = zip(l_file.read().splitlines(),
                       t_file.read().splitlines())

        for lemma, pos in combined:
            lemma = ''.join(lemma.split(' '))
            o_file.write(f'{lemma}\t{pos}\n')

        o_file.write('\n')


def file_to_set(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return set(x.split('\t')[0] for x in f.read().splitlines())
    
