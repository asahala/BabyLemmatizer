#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import conllutools as ct
import conlluplus
import preprocessing as pp
import model_api
from preferences import Paths
import postprocess

info = """===========================================================
Lemmatizer pipeline for BabyLemmatizer 2.0

asahala 2023
https://github.com/asahala

University of Helsinki
   Origins of Emesal Project
   Centre of Excellence for Ancient Near-Eastern Empires

==========================================================="""

def io(message):
    print(f'> {message}')

## TODO: READ context settigns from MODEL!"!!!!
CONTEXT = 1

class Lemmatizer:

    def __init__(self, input_file):
        path, file_ = os.path.split(input_file)
        f, e = file_.split('.')

        #fn = os.path.join(path, f)

        """ Path for saving intermediate files """
        step_path = os.path.join(path, 'steps')

        try:
            os.mkdir(step_path)
        except FileExistsError:
            pass
        
        fn = os.path.join(step_path, f)
        self.input_file = input_file
        self.word_forms = fn + '.forms'
        self.tagger_input = fn + '.tag_src'
        self.tagger_output = fn + '.tag_pred'
        self.lemmatizer_input = fn + '.lem_src'
        self.lemmatizer_output = fn + '.lem_pred'
        self.final_output = fn + '.final'
        self.line_count = 0
        self.segment_count = 1
        #self.preprocess_input(input_file)
        """ Load and normalize source CoNLL-U+ file """
        self.source_file = conlluplus.ConlluPlus(input_file, validate=False)
        self.preprocess_source()
        
        
    def preprocess_source(self):

        self.source_file.normalize()
        formctx = self.source_file.get_contexts('form')
        self.source_file.update_value('formctx', formctx)
        
        with open(self.tagger_input, 'w', encoding='utf-8') as pos_src,\
             open(self.word_forms, 'w', encoding='utf-8') as wf:
            io(f'Generating input data for neural net {self.input_file}')
            for form, formctx in self.source_file.get_contents('form', 'formctx'):
                pos_src.write(pp.make_tagger_src(formctx, context=CONTEXT) + '\n')
                wf.write(pp.get_chars(form + '\n'))
                self.line_count += 1
                
            #for stack in ct.get_training_data2(filename,
            #                    pp.clean_traindata):
            #    if stack == ct.EOU:
            #        f.write(ct.EOU[0] + '\n')
            #        wf.write(ct.EOU[0] + '\n')
            #        self.segment_count += 1
            #    else:
            #        f.write(pp.to_tagger_input(stack))
            #        wf.write(pp.get_chars(stack[1][0]) + '\n')
            #        self.line_count += 1
            io(f'Input file size: {self.line_count}'\
               f' words in {self.segment_count} segments.')

            
    def run_model(self, model_name, cpu):
        tagger_path = os.path.join(
            Paths.models, model_name, 'tagger', 'model.pt')
        lemmatizer_path = os.path.join(
            Paths.models, model_name, 'lemmatizer', 'model.pt')
        
        """ Run tagger on input """
        io(f'Tagging {self.tagger_input} with {model_name}')
        model_api.run_tagger(self.tagger_input,
                             tagger_path,
                             self.tagger_output,
                             cpu)

        """ Merge tags to make lemmatizer input """
        model_api.merge_tags(self.tagger_output,
                             self.source_file,
                             self.lemmatizer_input,
                             'xpos',
                             'xposctx')

        """ Run lemmatizer """
        io(f'Lemmatizing {self.lemmatizer_input} with {model_name}')
        model_api.run_lemmatizer(self.lemmatizer_input,
                                 lemmatizer_path,
                                 self.lemmatizer_output,
                                 cpu)

        """ Merge lemmata to CoNLL-U+ """
        model_api.merge_tags(self.lemmatizer_output,
                             self.source_file,
                             None,
                             'lemma',
                             None)

        ## TODO: fix path
        self.source_file.write_file(self.input_file.replace('.conllu', '_nn.conllu'))

        P = postprocess.Postprocessor(
            predictions = self.source_file,
            model_name = model_name)

        P.initialize_scores()
        P.fill_unambiguous(threshold = 0.7)
        P.disambiguate_by_pos_context(threshold = 0.7)

        self.source_file.force_value('xposctx', '_')
        self.source_file.force_value('formctx', '_')

        self.source_file.write_file(self.input_file.replace('.conllu', '_pp.conllu'), add_info=True)

        
if __name__ == "__main__":
    """ Demo for lemmatization """
    #l = Lemmatizer('./input/example.conllu')
    #l.run_model('lbtest1')
    pass



