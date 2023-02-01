import re


test = '[xx]x [x][x]x y[yyy]y xxx xxx'
stripped = re.sub('[\]\[]', '', test)
#print(stripped)

#                               0123456789
#ranges = get_substring_ranges('DUMU', stripped, end=0)


def interpolate(string, longer):
    if len(string) == 1:
        """ Avoid dividing with zero """
        return ''.join([string] + ['.'] * longer)
    
    out = ['.'] * longer
    shorter = len(string)
    for e, c in enumerate(string):
        out[e * (longer-1) // (shorter-1)] = c
    return ''.join(out)
    
def make_shape(string):
    return re.sub('[^\[\] ]', '_', string)

def substring_range(s, substring):
    for i in re.finditer(re.escape(substring), s):
        yield (i.start(), i.end())

def count_brackets(string):
    x = string.count('[')
    y = string.count(']')
    
    print(x+y, string)
    return x

def stretch(string, length, ranges):
    base = ''
    last = 0

    scomp = 0
    ecomp = 0
    for s, e in ranges:
        scomp += count_brackets(string[last:s])
        s += scomp
        base += string[last:s]
        ecomp += count_brackets(string[s:e]) + scomp
        e += ecomp
        base += '|' + interpolate(string[s:e], 7) + '|'
        last = e
    base += string[e:]
    print(string)
    print(base)

#s = stripped
#substring = "yyyyy"
#ranges = ([x for x in substring_range(s, substring)])

#print(make_shape(test))
#print(ranges)
#stretch(test, 0, ranges)



#def replace(source, target, xlit):
    





#replace('a-wi-lum', 'xxx-xxx-xxx', 'sum-ma a-wi-[lim in DU]MU a-[wi]-lim uh-ta-ap-pi-id')
BRACKETS = '[⸢⸣]'
DELIMITERS = '}{.:-'
ignore = '?!#*'

def get_bracket_flags(xlit_):
    """ Return bracket positions in xlit:
    final (-1), medial (1), initial (0) """

    #flags = [c for c in re.findall('.[%s].' % re.escape(
    #    BRACKETS+ignore), f'§{xlit_}§')
    xlit = '§' + xlit_ + '§'
    for e, c in enumerate(xlit_, start=1):
        if c in BRACKETS:
            if xlit[e+1] in DELIMITERS + ' §':
                yield (-1, xlit[e-1:e+2])
            elif xlit[e-1] in DELIMITERS + ' §':
                yield (0, xlit[e-1:e+2])
            else:
                yield (1, xlit[e-1:e+2])
        elif c in ignore:
            yield (-1, xlit[e-1:e+2])

for x in get_bracket_flags('a[n! sù]'):
    print(x)

for x in get_bracket_flags('din[g]? sù]'):
    print(x)
