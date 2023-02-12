import os
import copy
from collections import defaultdict
from preferences import Paths
import conlluplus as cplus

#=============================================================================

## TODO: tee lista yleisimmistä virheistä

## TODO: kokeile sanavektoreita monitulkintaisimpien logogrammien
## disambiguointiin

class Postprocessor:
    
    def __init__(self, predictions, model_name):
        self.model_name = model_name
        self.train = os.path.join(
            Paths.models, self.model_name,
            'conllu', 'train.conllu')

        """ Container for the last post-processing step """
        self.predictions = predictions
        self.train_data = None
        
    def _generate_lemmadict(self, fields, threshold):
        """ Creates naive disambiguation dictionary based on
        FORM + an arbitrary tag mapped to a lemma """
        ## TODO: koita parantaa postägäystä, esim
        ## xlit + left context + right context --> lemma + POS
        lems = defaultdict(dict)
        if self.train_data is None:
            self.train_data = cplus.ConlluPlus(self.train, validate=False)

        for data in self.train_data.get_contents():
            key1 = data[fields[0]]
            key2 = data[fields[1]]
            lemma = data[2]            
            lems[(key1, key2)].setdefault(lemma, 0)
            lems[(key1, key2)][lemma] += 1
                                                                            
        """ Collect lemmas that have been given to xlit + pos
        more often than the given threshold """
        for xlit_pos, lemmata in lems.items():

            for lemma, count in lemmata.items():
                score = count / sum(lemmata.values())
                if score >= threshold:
                    yield xlit_pos, lemma, 1.0 #score; now flat not

                    
    def initialize_scores(self):
        """ Initialize confidence scores """
        oov = set()
        with open(os.path.join(Paths.models, self.model_name,
                               'override', 'test-types-oov.xlit')) as f:
            for line in f:
                line = line.rstrip()
                oov.add(line.split('\t')[0])

        def get_scores():
            for sentence in self.predictions.get_contents():
                form = sentence[cplus.FORM]
                if form in oov:
                    if form.lower() == form:
                        score = 2.0
                    elif form.upper() == form:
                        score = 0.0
                    else:
                        score = 1.0
                else:
                    score = 3.0
                yield score
                
        self.predictions.update_value(
            field = 'score', values = get_scores())
        
                
    def fill_unambiguous(self, threshold=0.9):
        """ First post-processing step: calculate close-to
        unambiguous word forms + pos tags from the training
        data and overwrite lemmatizations

        :param threshold        unambiguity threshold
        :type threshhold        float """
                        
        print(f'> Post-processor ({self.model_name}): '\
              f'filling in unambiguous words (t ≥ {threshold})')

        """ Reform dictionary in format 
           {(input fields): 
               {output_index: output, score: score}, ...} """
        unambiguous = {xlit_pos : {cplus.LEMMA: lemma, 'score': score}
                       for xlit_pos, lemma, score in self._generate_lemmadict(
                               fields=(cplus.FORM, cplus.XPOS), threshold=threshold)}

        """ Populate CoNLL-U with substitutions """
        self.predictions.conditional_update_value(
            unambiguous, fields = ('form', 'xpos'))


    def disambiguate_by_pos_context(self, threshold=0.9):
        """ Disambiguate lemmata by their XPOS context; works
        just as fill_unambiguous() but uses XPOS context instead of
        XPOS as second part of the key. """

        ## TODO: tee tämä steppi ensin ja koita vaihtaa pos-tägi.
        ## Ei kyllä toimi jos konteksti on vituillaan
        ## Markovin ketju? 
        
        unambiguous = {xlit_pos : {cplus.LEMMA: lemma, 'score': score}
                       for xlit_pos, lemma, score in self._generate_lemmadict(
                               fields=(cplus.FORM, cplus.XPOSCTX), threshold=threshold)}  

        self.predictions.conditional_update_value(
            unambiguous, fields = ('form', 'xposctx'))
        
        
        
    
if __name__ == "__main__":
    P = Postprocessor('input/example_nn.conllu.final', 'lbtest1')
    P.disambiguate_by_pos_context()
