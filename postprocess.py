import os
import copy
from collections import defaultdict
from preferences import Paths
import conllutools as ct

#=============================================================================

## TODO: tee lista yleisimmistä virheistä

## TODO: kokeile sanavektoreita monitulkintaisimpien logogrammien
## disambiguointiin

class SubstitutionAlgorithm:
    
    @classmethod
    def best_if_not_topn(cls, data, substitutions):

        #for index, substitution in substitutions.items():
        #    if data[index] in substitution:
        #        return data, substitution[data[index]]
                
        for index, substitution in substitutions.items():
            data[index] = max(substitution, key=substitution.get)
            score = substitution[data[index]]

        return data, score
    
    
class Postprocessor:
    
    def __init__(self, filename, model_name):
        self.filename = filename
        self.model_name = model_name
        self.train = os.path.join(
            Paths.models, self.model_name,
            'conllu', 'train.conllu')
        """ Container for the last post-processing step """
        self.last_step = ((line.split('\t'), 0.0) for line in ct.read_conllu(
                                  self.filename, only_data=True))
        
    def populate(self, source, mappings, in_fields):
        """ Populates source CoNLL-U with corrected annotations

        :param source          Source conllu data lines
        :param mappings        Substitution mapping dictionary
        :param in_fields       CoNNL-U indices that are fed into
                               the substituion mappings

        :type source           iterable
        :type mappings         dictionary
        :type in_fields        tuple 

        this function yields substituted CoNLL-U line and
        its confidence score. """
        step_score = 0
        step_subs = 0
        for e, line in enumerate(source):
            data, score = line
            key = tuple(data[index] for index in in_fields) 
            substitutions = mappings.get(key, None)

            if substitutions is not None:
                #data, add_score = algorithm(data, substitutions)                
                for index, sub in substitutions.items():
                    if isinstance(index, int):
                        if data[index] != sub:
                            step_subs += 1
                        data[index] = sub
                        
                score += substitutions['score']
                
            step_score += score
            yield (data, score)

            
        print(f'  + Step score: {round(step_score / e, 2)} '\
              f'Substitutions: {step_subs} '\
              f'({round(100*step_subs / e, 2)}%)')

                    
    def fill_unambiguous(self, threshold=0.4):
        """ First post-processing step: calculate close-to
        unambiguous word forms + pos tags from the training
        data and overwrite lemmatizations

        :param threshold        unambiguity threshold
        :type threshhold        float """
        
        def generate_lemmadict():
            """ Collect xlit : lemma + POS relations from train data """
            lems = defaultdict(dict)
            for fields in ct.read_conllu(self.train, only_data=True):
                xlit, lemma, pos = fields.split('\t')[1:4]
                lems[(xlit, pos)].setdefault(lemma, 0)
                lems[(xlit, pos)][lemma] += 1

            """ Collect lemmas that have been given to xlit + pos
            more often than the given threshold """
            for xlit_pos, lemmata in lems.items():
                #best = []
                for lemma, count in lemmata.items():
                    score = count / sum(lemmata.values())
                    if score >= threshold:
                        yield xlit_pos, lemma, score#best.append((score, lemma))
                #if best:
                #    yield (xlit_pos, best)
                
        print(f'> Post-processor ({self.model_name}): filling in unambiguous words (t ≥ {threshold})')

        """ Reform dictionary in format 
           {(input fields): 
               {output_index: output, score: score}, ...} """
        #unambiguous = defaultdict(list)
        #for entry in generate_lemmadict():
        #    xlit_pos, best = entry
        #    scores, lemmas = zip(*sorted(best, reverse=True))
        #    unambiguous[xlit_pos] = {ct.LEMMA: {l: s for l, s in zip(lemmas, scores)}}

        unambiguous = {xlit_pos : {ct.LEMMA: lemma, 'score': score} for xlit_pos, lemma, score in generate_lemmadict()}

        self.last_step = self.populate(
            source = self.last_step,#self.last_step,
            mappings = unambiguous,
            in_fields = (ct.FORM, ct.UPOS))#SubstitutionAlgorithm.best_if_not_topn)

        
    def disambiguate_by_pos_context(self):
        pass

    
if __name__ == "__main__":
    
    P = Postprocessor('conllu/lbtest6-test.conllu',
                      'lbtest1')
    P.fill_unambiguous()
    print(P.XX)
    for x in P.last_step:
        pass
    print(P.XX)
