#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import conllutools as ct
import preprocessing as pp
import model_api

info = """===========================================================
Lemmatizer pipeline for BabyLemmatizer 2

asahala 2023
https://github.com/asahala

University of Helsinki
   Origins of Emesal Project
   Centre of Excellence for Ancient Near-Eastern Empires

==========================================================="""

def io(message):
    print(f'> {message}')


class Lemmatizer:

    def __init__(self, input_file):
        path, file_ = os.path.split(input_file)
        f, e = file_.split('.')

        #fn = os.path.join(path, f)
        
        step_path = os.path.join(path + '/steps')
        try:
            os.mkdir(step_path)
        except FileExistsError:
            pass
        
        fn = os.path.join(step_path, f)
        
        self.source_file = input_file
        self.word_forms = fn + '.forms'
        self.tagger_input = fn + '.tag_src'
        self.tagger_output = fn + '.tag_pred'
        self.lemmatizer_input = fn + '.lem_src'
        self.lemmatizer_output = fn + '.lem_pred'
        self.final_output = fn + '.final'
        self.line_count = 0
        self.segment_count = 1
        self.preprocess_input(input_file)
        
    def preprocess_input(self, filename):
        print('\n' + info + '\n')
        with open(self.tagger_input, 'w', encoding='utf-8') as f,\
             open(self.word_forms, 'w', encoding='utf-8') as wf:
            io(f'Preprocessing {filename}')
            for stack in ct.get_training_data2(filename,
                                pp.clean_traindata):
                if stack == ct.EOU:
                    f.write(ct.EOU[0] + '\n')
                    wf.write(ct.EOU[0] + '\n')
                    self.segment_count += 1
                else:
                    f.write(pp.to_tagger_input(stack))
                    wf.write(pp.get_chars(stack[1][0]) + '\n')
                    self.line_count += 1
            io(f'Input file size: {self.line_count}'\
               f' words in {self.segment_count} segments.')

    def run_model(self, model_name):
        tagger_path = f'./models/{model_name}/tagger/model_step_35000.pt'
        lemmatizer_path = f'./models/{model_name}/lemmatizer/model_step_35000.pt'

        io(f'Tagging {self.tagger_input} with {model_name}')
        model_api.run_tagger(self.tagger_input,
                             tagger_path,
                             self.tagger_output)

        model_api.merge_tags(self.tagger_output,
                             self.word_forms,
                             self.lemmatizer_input)

        io(f'Lemmatizing {self.lemmatizer_input} with {model_name}')
        model_api.run_lemmatizer(self.lemmatizer_input,
                                 lemmatizer_path,
                                 self.lemmatizer_output)
       

        model_api.merge_to_final(self.tagger_output,
                                 self.lemmatizer_output,
                                 self.final_output)

        final = self.source_file.replace('.conllu', '_lemmatized.conllu')
        ct.make_conllu(self.final_output,
                       self.source_file,
                       final)

        io(f'Annotations saved to {final}')
        
l = Lemmatizer('./input/example.conllu')
l.run_model('lbtest1')
