import os
from preferences import Paths

"""
1. Store override as conllu
2. concatenate 
 --> can be used automatically by postprocessor
"""

def read_override(model_name):
    override_files = (f for f in os.listdir(
        os.path.join(Paths.override, model_name)) if f.endswith('.tsv'))

    
                                             
read_override('lbtest2')
