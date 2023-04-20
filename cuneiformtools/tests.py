import re

def is_numeral(form):

    if form.isdigit():
        return 'num_cardinal'
    if form.replace('.', '').isdigit():
        return 'num_cardinal'
    if form[0].isdigit() and 'kam' in form.lower():
        return 'num_ordinal'
    if form[0].isdigit() and '.la' in form.lower():
        return 'num_cardinal'
    
    return False

def is_lacuna(form):

    signs = re.split('[-\.]', form)
    if signs:
        degree = round(signs.count('x') / len(signs),2)
    else:
        degree = 0
    #print(degree)
    
    if set([x for x in form if x.isalpha()]) == set('x'):
        return 'lacuna_small'
    if '...' in form:
        return 'lacuna_large'
    if degree > 0:
        return f'lacuna_partial:{degree}'
        
    return False

