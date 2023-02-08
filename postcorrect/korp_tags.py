
""" Map Korp-POS tags to abbreviations """
korp_pos_tags = {'verb': 'VERB',
                 'commonnoun': 'NOUN',
                 'pronoun': 'PRON',
                 'number': 'NUM',
                 'adverb': 'ADV',
                 'propernoun': 'PROPN',
                 'prepositionpostposition': 'ADP',
                 'interjection': 'INTJ',
                 'miscellaneousundetermined': 'UNK',
                 'particle': 'PART',
                 'adjective': 'ADJ',
                 'conjunction': 'CONJ'}

def map_to_korp(pos):
    tag = korp_pos_tags.get(pos, 'NULL')
    if tag == 'NULL':
        pass#print('Warning: Unknown Korp POS tag: %s' % pos)
    return tag
