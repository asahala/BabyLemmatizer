import re
import json

""" Indices

0       1     2     3    4
wordid  xlit  lemma pos  pos|

"""

#with open('../models/assyrian/override.json', 'r', encoding='utf-8') as f:
#    override_dict = json.load(f)

def override(line):
    """ This is for Assyrian data in case it has been lemmatized with
    a babylonian model. This will replace all word forms with Assyrian
    lemmas as the neural parser may have labeled them with the Babylonian
    ones """
    oride = override_dict.get(line[1], None)

    if oride is None:
        return line

    lemma, pos = oride

    line[2] = lemma
    line[3] = pos
    line[4] = pos + '|empty'
    line[5] = '_'
    line[-1] = '1.5'
    return line

def capitalize_names(line):
    if line[1].startswith(('{m}', '{f}', '{d}')):
        line[2] = line[2][0].upper() + line[2][1:]
    return line

def revert_dates(line):
    if re.match('UD[\.-](\d+?|x|X|n|N)([\.-]KAM)?.*', line[1]):
        line[2] = '_'
        line[3] = '_'
        line[4] = '_'
        line[5] = '_'
        line[-1] = 'date'
    return line

def revert_divs(line):
    if line[1] == '_':
        line[2] = '_'
        line[3] = '_'
        line[4] = '_'
        line[5] = '_'
        line[-1] = 'div'
    return line

def revert_numbers(line):
    """ Unlemmatize fractions and ordinal/cardinal numbers """
    if line[1].replace('/', '').isdigit()\
       or (line[1][0].isdigit() and line[1].endswith(('zKAM', 'zKAM₂')))\
       or re.match('(\d\.)+', line[1]):
        line[2] = '_'
        line[3] = 'n'
        line[4] = 'n|empty'
        line[5] = '_'
        line[-1] = 'num'
    return line

def revert_slash(line):
    """ Unlemmatize / and // """
    if line[1].startswith('/'):
        line[2] = '_'
        line[3] = '_'
        line[4] = '_'
        line[5] = '_'
        line[-1] = 'gap'
    return line

def revert_lacunae(line):
    """ Unlemmatize too broken words """
    if 'x' not in line[1] and '...' not in line[1]:
        return line

    lacuna = False
    # Give up with long breakages
    if '...' in line[1]:
        lacuna = True
    if 'x-x-x' in line[1]:
        lacuna = True

    if lacuna:
        line[2] = '_'
        line[3] = 'u'
        line[4] = 'u|empty'
        line[5] = '_'
        line[-1] = 'lac'
        return line
    
    chars = re.sub('(\{.+?\}|-|\.|\.MEŠ|\.HI\.A)', '', line[1])
    broken_chars = chars.count('x')
    
    if set(chars) == set('x') or len(chars) - broken_chars < 2:
        line[2] = '_'
        line[3] = 'u'
        line[4] = 'u|empty'
        line[5] = '_'
        line[-1] = 'lac'
    return line

def correct_all(line):
    elems = line.split('\t')
    if len(elems) < 11:
        return line
    else:
        for func in [revert_numbers,
                     revert_dates,
                     revert_lacunae,
                     revert_divs,
                     revert_slash, 
                     capitalize_names
                    ]: #override if assyrian
            elems = func(elems)
            
    return '\t'.join(elems)
    
def process(data):
    for line in data:
        yield correct_all(line)
        
