#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
#import conllutools as ct
import conlluplus
import preprocessing as pp
import model_api
from preferences import Paths, Tokenizer, Context
import postprocess

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

## TODO: READ context settigns from MODEL!"!!!!
#CONTEXT = Context.pos_context

class Lemmatizer:

    def __init__(self, input_file, fast=False, ignore_numbers=True):
        path, file_ = os.path.split(input_file)
        f, e = file_.split('.')

        #fn = os.path.join(path, f)

        """ Path for saving intermediate files """
        step_path = os.path.join(path, 'steps')

        try:
            os.mkdir(step_path)
        except FileExistsError:
            pass

        """ Parameters """
        self.ignore_numbers = ignore_numbers
        
        fn = os.path.join(step_path, f)
        self.backup_file = os.path.join(path, f'backup_{f}.conllu')
        self.fast = fast
        self.input_file = input_file
        self.input_path = path
        self.word_forms = fn + '.forms'
        self.tagger_input = fn + '.tag_src'
        self.tagger_output = fn + '.tag_pred'
        self.lemmatizer_input = fn + '.lem_src'
        self.lemmatizer_output = fn + '.lem_pred'
        self.final_output = fn + '.final'
        self.line_count = 0
        self.segment_count = 0
        #self.preprocess_input(input_file)
        """ Load and normalize source CoNLL-U+ file """
        self.source_file = conlluplus.ConlluPlus(input_file, validate=False)
                
        
    def preprocess_source(self):
        
        self.source_file.normalize()
        formctx = self.source_file.get_contexts('form', size=Context.tagger_context)
        self.source_file.update_value('formctx', formctx)
        
        with open(self.tagger_input, 'w', encoding='utf-8') as pos_src,\
             open(self.word_forms, 'w', encoding='utf-8') as wf:
            io(f'Generating input data for neural net {self.input_file}')
            for id_, form, formctx in self.source_file.get_contents('id', 'form', 'formctx'):
                pos_src.write(
                    pp.make_tagger_src(formctx, context=Context.tagger_context) + '\n')
                wf.write(pp.get_chars(form + '\n'))
                self.line_count += 1
                if id_ == '1':
                    self.segment_count += 1
            io(f'Input file size: {self.line_count}'\
               f' words in {self.segment_count} segments.')


    def update_model(self, model_name):
        overrides = [os.path.join(self.input_path, f) for f\
                     in os.listdir(self.input_path) if f.endswith('.tsv')]
                
        if overrides:
            mod_o = os.path.join(
                Paths.models, model_name, 'override', 'override.conllu')
            override = conlluplus.ConlluPlus(mod_o, validate=False)
            for o_file in overrides:
                override.read_corrections(o_file)
                override.normalize()
                os.remove(o_file) # this is bad
            override.write_file(mod_o)

            
            
    def run_model(self, model_name, cpu):

        """ Read Tokenizer Preferences """
        Tokenizer.read(model_name)
        Context.read(model_name)
        
        """ Update model override """
        self.update_model(model_name)

        """ Load and normalize source CoNLL-U+ file """
        self.source_file = conlluplus.ConlluPlus(
            self.input_file, validate=False)
        
        """ Backup for write-protected fields """
        pp_file = self.input_file.replace('.conllu', '_pp.conllu')
        if os.path.isfile(pp_file):
            is_backup = True
            shutil.copy(pp_file, self.backup_file)
        else:
            is_backup = False
            
        """ Preprocess data for lemmatization """
        self.preprocess_source()
                
        """ Set model paths """
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

        self.source_file.write_file(
                self.input_file.replace('.conllu', '_nn.conllu'))

        #""" Merge backup """
        #pass
        
        """ Initialize postprocessor """
        P = postprocess.Postprocessor(
            predictions = self.source_file,
            model_name = model_name)

        P.initialize_scores()
        P.fill_unambiguous(threshold = 0.6)
        P.disambiguate_by_pos_context(threshold = 0.6)
        P.apply_override()
        
        if self.ignore_numbers:
            self.source_file.unlemmatize(numbers=True)

        """ Temporary field cleanup """
        self.source_file.force_value('xposctx', '_')
        self.source_file.force_value('formctx', '_')
        
        self.source_file.write_file(
            self.input_file.replace('.conllu', '_pp.conllu'), add_info=True)

        """ Merge backup """
        print('> Merging manual corrections')
        #if is_backup:
        #    conlluplus.merge_backup(self.backup_file, pp_file)
            
        """ Write lemmalists """
        self.source_file.make_lemmalists()
        

    def override_cycle(self):
        """ Lemmatization cycle """
        filename, ext = os.path.splitext(self.filename)
        
        
        
if __name__ == "__main__":
    """ Demo for lemmatization """
    #l = Lemmatizer('./input/example.conllu')
    #l.run_model('lbtest1')
    pass



