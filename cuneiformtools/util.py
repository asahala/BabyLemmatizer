#!/usr/bin/python
# -*- coding: utf-8 -*-

""" CuneiformTools Utilities                      

asahala 2021
https://github.com/asahala/

"""

import sys
import re
from functools import lru_cache
from cuneiformtools.alphabet import INDEX, ALPHABET, REMOVE_INDEX,\
     ASCII_INDEX, ZERO, DELIMITERS, PIPE, BRACKETS, ALLALPHA


def sort(array, sort_index=0):
    """ Sorts cuneiform signs or transliterated/transcribed
    words alphabetically

    :param array             list to be sorted
    :param sort_index        if sorting list of lists, define
                             by which item the list is sorted

    :type array              list (of strings or lists/tuples)
    :type sort_index         int

    """

    if not array:
        return array

    def validate(text):
        """ Sort input validator. Reveal undefined characters """
        def scan(string):
            for c in string:
                if c not in ALPHABET:
                    print('--> %s in <%s>' % (c, string))
        
        if isinstance(text, str):
            scan(text)
        if isinstance(text, (list, tuple)):
            for word in text:
                scan(word)
        else:
            print('validate() arg must be string or list/tuple of strings.')

    def sort_alpha(array):
        array = [zero_fill(x) for x in array]
        try:
            return sorted(array, key=lambda item:
                          [ALPHABET.index(char) for char in item])
        except ValueError:
            print("Unable to sort due to unknown alphabet:")
            validate(array)
            print("Add symbols to alphabet.py definitions.")
            return array

    def un_zero_fill(string):
        return string.replace(ZERO, '')

    def zero_fill(string):
        """ Fill indices with leading zeros """
        outstring = ''
        i = len(string) - 1
        last = '_'
        for c in reversed(string):
            c_out = c
            if c in INDEX and last not in INDEX:
                if string[i-1] not in INDEX:
                    c_out = c + ZERO
            outstring += c_out
            last = c
            i -= 1
        return outstring[::-1]

    if not isinstance(array, (list, tuple)):
        print(f'Sort lists or tuples, not {type(array)}')
        return None
    if isinstance(array[0], str):
        array = [un_zero_fill(x) for x in sort_alpha(array)]
    if isinstance(array[0], (list, tuple)):
        order = {}
        for item in array:
            try:
                order.setdefault(item[sort_index], []).append(item)
            except IndexError:
                print('Cannot sort: sort_index (%i) exceeds'\
                      ' longest sublist.' % sort_index)
                sys.exit(0)
                
        array = []
        for key in [un_zero_fill(x) for x in sort_alpha(order.keys())]:
            array.extend(order[key])
        
    return array


def tokenize(line):
    return line.split(' ')


def unzip_xlit(xlit, extra_delimiters=''):
    """ Return signs and delimiters as separate lists. Note
    that combina

    {d}en-líl-lá   -->     signs:     0 d en líl la
                           delims:     { }  -   -

    [im]-è(|UD.DU|){+i-e}  signs:     i[m] è(|UD.DU|)  i e
                           delims:        -          {+ - }

    where 0 stands for empty string. Note that by default
    this function does not tokenize lines.

    :param word          input word in transliteration
    :param extra_delims  any extra single-char delimiters
    :type word           str
    :type extra_delims   str

    """
    
    m_dict = {'†': '{+'}
    delims_ = DELIMITERS + ' ' + extra_delimiters 
    xlit = re.sub('\.\.+', '…', xlit)

    for k, v in m_dict.items():
        xlit = xlit.replace(v, k)
        delims_ += k

    sign = ''
    signs = []
    delimiters = []

    pipe = ''
    for c in xlit:
        if c in delims_:
            if not pipe:
                c = m_dict.get(c, c)
                signs.append(sign)
                delimiters.append(c)
                sign = ''
            else:
                sign += c
        elif c == PIPE:
            sign += c
            if not pipe:
                pipe = c
            else:
                pipe = ''
        elif c == '…':
            sign += '...'
        else:
            sign += c
    if sign:
        signs.append(sign)

    return signs, delimiters
        

def zip_xlit(signs, delimiters):
    """ Zip signs and delimiters back into words

    :param word          input word in transliteration
    :type word           str

    """
    
    word = ''
    for c in '_'.join(signs):
        if c == '_':
            word += delimiters.pop(0)
        else:
            word += c

    for d in delimiters:
        word += delimiters.pop(0)

    return word


class Transducer_OLD:

    """ A transducer for bracket-sensitive substitutions.
    Consume input string character by character and either
    write or transduce them on the output tape;

    source and target must be interpolated or chunked to
    same length.

    E.g. a substitution pair {d}HAR : {d}SAGGAR will replace

        {d}HA[R-DU3] with  {d}SAGG[AR-DU3]
       {[d}HA]R-DU3  with {[d}SAGG]AR-DU3

    etc. """

    def __init__(self, ignore, boundary='§'):
        self.ignore = ignore
        self.boundary = boundary
        self._compile_regex()

    def _compile_regex(self):
        """ Post-correction regexes in order; these try
        to fix errors caused by extreme length difference
        between source and target strings.

        1. Shift left bracket to left if x[]

        2. Shift left bracket to left if preceded
           by delimiter: x-]x --> x]-x

        3. Shift left bracket to right if followed
           by closing determinative: [}x --> }[x

        4. Shift left bracket if around index: xx[12] -> x[x12]
        
        5. Shift unallowed symbols from medial position
           to the next delimiter: x!x- --> xx!-

        6. Move right bracket right if followed by ignore
           symbols and delimiters: [x]!?- --> [x!?]-
        
        """

        ## TODO: rewrite replace to avoid these mistakes
        
        _DEL_ = re.escape(DELIMITERS + ' ')
        _IGN_ = re.escape(self.ignore)
        _ALPHA_ = re.escape(ALLALPHA)
        _LEFT_ = '\[|⸢|<'
        _RIGHT_ = '\]|⸣|>'

        self.regex = [
            (re.compile(f'(.)({_LEFT_})({_RIGHT_})'), r'\2\1\3'),
            (re.compile(f'([^\.])([{_DEL_}])({_RIGHT_})'), r'\1\3\2'),
            (re.compile('(%s)(})' % _LEFT_), r'\2\1'),
            (re.compile(f'([{_ALPHA_}])({_LEFT_})(\d+)({_RIGHT_})([{_DEL_}$])'), r'\2\1\3\4\5'),
            (re.compile(f'([{_IGN_}])([^{_DEL_}]+?)([{_DEL_}$])'), r'\2\1\3'),
            (re.compile(f'({_RIGHT_})([{_IGN_}]+?)([{_DEL_}])'), r'\2\1\3')]
        
    def _reset_tapes(self):
        self.tmp_out_tape = {'orig': [], 'trans': []}
        self.s_ = self.source.copy()
        self.t_ = self.target.copy()

    def _write_to_output_tape(self, tape):
        self.output_tape += tape
        self._reset_tapes()

    def interpolate(self):
        pass

    def chunk(self):
        pass

    def cleanup(self, output_tape):
        """ Apply compiled regular expression to output """
        output_tape = ''.join(output_tape).replace(self.boundary, '')

        for patt, repl in self.regex:
            output_tape = re.sub(patt, repl, output_tape)
        
        return output_tape        

    def run(self, source, target, xlit, sign=False):

        if not xlit:
            return xlit
        
        """ Mark left and right boundaries for sign
        replacement to force full matches """
        if sign:
            self.xlit = self.boundary + xlit + self.boundary
            self.source = [self.boundary] + source + [self.boundary]
            self.target = [self.boundary] + target + [self.boundary]

        else:
            self.source = source
            self.target = target
            self.xlit = xlit

        """ Initialize tapes """
        self.output_tape = []
        self._reset_tapes()
       
        for c in self.xlit:

            if c in BRACKETS + '<>' + self.ignore:
                self.tmp_out_tape['orig'].append(c)
                self.tmp_out_tape['trans'].append(c)
                continue

            self.tmp_out_tape['orig'].append(c)

            if c == self.s_[0]:
                """ Transduce from source alphabet to target
                alphabet """
                c_orig = c
                c_trans = self.t_.pop(0)
                self.s_.pop(0)
                #print(c, c_trans, '_',  self.tmp_out_tape, sep='\t')
                self.tmp_out_tape['trans'].append(c_trans)
            else:
                """ Reject output tape """
                #print(c, c, 'rej', self.tmp_out_tape, sep='\t')
                self._write_to_output_tape(self.tmp_out_tape['orig'])

            if not self.s_:
                """ Accept output tape """
                #print(c, c_trans, 'acc', self.tmp_out_tape, sep='\t')                        
                self._write_to_output_tape(self.tmp_out_tape['trans'])
                
        self._write_to_output_tape(self.tmp_out_tape['orig'])

        return self.cleanup(self.output_tape)

class Transducer:

    """ A transducer for bracket-sensitive substitutions.
    Consume input string character by character and either
    write or transduce them on the output tape;

    source and target must be interpolated or chunked to
    same length.

    E.g. a substitution pair {d}HAR : {d}SAGGAR will replace

        {d}HA[R-DU3] with  {d}SAGG[AR-DU3]
       {[d}HA]R-DU3  with {[d}SAGG]AR-DU3

    etc. """

    def __init__(self, ignore, boundary='§'):
        self.ignore = ignore
        self.boundary = boundary
        self._compile_regex()

    def _compile_regex(self):
        """ Post-correction regexes in order; these try
        to fix errors caused by extreme length difference
        between source and target strings.

        1. Shift left bracket to left if x[]

        2. Shift left bracket to left if preceded
           by delimiter: x-]x --> x]-x

        3. Shift left bracket to right if followed
           by closing determinative: [}x --> }[x

        4. Shift left bracket if around index: xx[12] -> x[x12]
        
        5. Shift unallowed symbols from medial position
           to the next delimiter: x!x- --> xx!-

        6. Move right bracket right if followed by ignore
           symbols and delimiters: [x]!?- --> [x!?]-
        
        """

        ## TODO: rewrite replace to avoid these mistakes
        
        _DEL_ = re.escape(DELIMITERS + ' ')
        _IGN_ = re.escape(self.ignore)
        _ALPHA_ = re.escape(ALLALPHA)
        _LEFT_ = '\[|⸢|<'
        _RIGHT_ = '\]|⸣|>'

        self.regex = [
            (re.compile(f'(.)({_LEFT_})({_RIGHT_})'), r'\2\1\3'),
            (re.compile(f'([^\.])([{_DEL_}])({_RIGHT_})'), r'\1\3\2'),
            (re.compile('(%s)(})' % _LEFT_), r'\2\1'),
            (re.compile(f'([{_ALPHA_}])({_LEFT_})(\d+)({_RIGHT_})([{_DEL_}$])'), r'\2\1\3\4\5'),
            (re.compile(f'([{_IGN_}])([^{_DEL_}]+?)([{_DEL_}$])'), r'\2\1\3'),
            (re.compile(f'({_RIGHT_})([{_IGN_}]+?)([{_DEL_}])'), r'\2\1\3')]
        
    def _reset_tapes(self):
        self.tmp_out_tape = {'orig': [], 'trans': []}
        self.s_ = self.source.copy()
        self.t_ = self.target.copy()

    def _write_to_output_tape(self, tape):
        self.output_tape += tape
        self._reset_tapes()

    def interpolate(self):
        pass

    def chunk(self):
        pass

    def cleanup(self, output_tape):
        """ Apply compiled regular expression to output """
        output_tape = ''.join(output_tape).replace(self.boundary, '').replace('_', '')

        return output_tape
        
        #for patt, repl in self.regex:
        #    output_tape = re.sub(patt, repl, output_tape)
        # 
        r#eturn output_tape        

    def run(self, source, target, xlit, word=False):

        if not xlit:
            return xlit
        
        """ Right-pad input transliteration to mark end of
        the segment """
        if word:
            self.xlit = '_' + xlit + '_' + self.boundary
            self.source = ['_'] + source + ['_']
            self.target = ['_'] + target + ['_']
        else:
            self.xlit = xlit + self.boundary
            self.source = source
            self.target = target
        
        """ Initialize tapes """
        self.output_tape = []
        self._reset_tapes()

        last = '§'
        for e, c in enumerate(self.xlit):

            if c == '§':
                continue

            if c in BRACKETS + '<>' + self.ignore:
                self.tmp_out_tape['orig'].append(c)
                self.tmp_out_tape['trans'].append(c)
                continue

            next_ = self.xlit[e+1:]            
            self.tmp_out_tape['orig'].append(c)

            if c == self.s_[0]:
                """ Transduce from source alphabet to target
                alphabet """
                c_orig = c
                c_trans = self.t_.pop(0)
                self.s_.pop(0)
                #print(c, c_trans, '_',  self.tmp_out_tape, sep='\t')
                self.tmp_out_tape['trans'].append(c_trans)
            else:
                """ Reject output tape """
                #print(c, c, 'rej', self.tmp_out_tape, sep='\t')
                self._write_to_output_tape(self.tmp_out_tape['orig'])

            if not self.s_:
                """ Accept output tape """
                #print(c, c_trans, 'acc', self.tmp_out_tape, sep='\t')

                """ Scan for next delimiter to make sure that
                partial replacements are not accepted """
                for char in next_:
                    if char in DELIMITERS + '§ ':
                        next_ = '§'
                        break
                    elif char in self.ignore + '⸣>]':
                        continue
                    else:
                        next_ = ''
                        break

                if (next_ == '§' and last in DELIMITERS + '§ ') or c in DELIMITERS + ' §':
                    self._write_to_output_tape(self.tmp_out_tape['trans'])
                else:
                    self._write_to_output_tape(self.tmp_out_tape['orig'])

            if not self.tmp_out_tape['trans']:
                last = c
            
        self._write_to_output_tape(self.tmp_out_tape['orig'])
        
        return self.cleanup(self.output_tape)

tr = Transducer(ignore='!?#*')

@lru_cache(maxsize=256)
def replace_OLD(source, target, xlit, sign=False, ignore=''):

    """ Replace strings in transliteration preserving
    bracket positions.
        
    :param source          what to replace
    :param target          replace with this
    :param xlit            input transliteration
    :param sign            constrain substitutions to full signs
    :param ignore          ignored characters

    :type source           str
    :type target           str
    :type xlit             str
    :type sign             bool
    :type ignore           str
    
    """

    strip_xlit = ''.join([c for c in xlit if c not in BRACKETS+'<>'+ignore])

    """ Ignore lines that have nothing to replace for efficiency """
    c = strip_xlit.count(source)
    if c == 0:
        return xlit


    """ Skip computationally heavier operations if brackets
    do not exist """
    if strip_xlit == xlit:
        if sign:
            signs, delimiters = unzip_xlit(xlit, extra_delimiters=' ')
            signs = [re.sub(f'^{source}$', target, s) for s in signs]
            return zip_xlit(signs, delimiters)
        else:
            parts = []
            for t in xlit.split(' '):
                parts.append(re.sub('^' + source + '$', target, t))
            return ' '.join(parts)

    ## MOVE THESE TO TRANSDUCER
    def interpolate(string, longer):
        """ Interpolate source and target strings to same length,
        e.g. dingir : AN --> dingir : A^^^^N """

        if len(string) == 1:
            """ Avoid dividing with zero """
            return [string] + [''] * longer
        
        out = [''] * longer
        shorter = len(string)
        for e, c in enumerate(string):
            out[e * (longer-1) // (shorter-1)] = c
        return out

    def chunk(string, shorter):
        """ Chunk target into multichar strings if source is
        shorter, e.g. AN : dingir --> AN : din^gir """
        
        string = list(tuple(target))
        k, m = divmod(len(string), shorter)
        return list(''.join(string[i*k+min(i, m):(i+1)*k+min(i+1, m)])
                 for i in range(shorter))

    """ Interpolate or chunk """
    if len(source) > len(target):
        target = interpolate(target, len(source))
    elif len(source) < len(target):
        target = chunk(target, len(source))
        if len(target) != len(source):
            print('Bad juju', source, target)
    else:
        target = list(tuple(target))
    source = list(tuple(source))

    """ Initialize trasducer """

    if sign:
        """ Sign-level substitutions, e.g. en : X will change
        en-engar into X-engar """
        t, d = unzip_xlit(xlit, extra_delimiters=' ')
        parts = []
        for token in t:
            #tr = Transducer(source, target, token, ignore)
            parts.append(tr.run(source, target, token, sign))
        return (zip_xlit(parts, d))
    else:
        tokens = tokenize(xlit)
        parts = []
        for token in tokens:
            parts.append(tr.run(source, target, token, sign=True))
        return ' '.join(parts)
        

    '''
    else:
        """ Free substitutions, e.g. en : X will change
        en-engar X-Xgar """
        tokens = tokenize(xlit)
        parts = []
        
        #tr = Transducer(source, target, xlit, ignore)
        return tr.run(source, target, xlit, sign)'''


@lru_cache(maxsize=256)
def replace(source, target, xlit, word=False, ignore=''):

    """ Replace strings in transliteration preserving
    bracket positions.
        
    :param source          what to replace
    :param target          replace with this
    :param xlit            input transliteration
    :param sign            constrain substitutions to full signs
    :param ignore          ignored characters

    :type source           str
    :type target           str
    :type xlit             str
    :type sign             bool
    :type ignore           str
    
    """

    ## MOVE THESE TO TRANSDUCER
    def interpolate(string, longer):
        """ Interpolate source and target strings to same length,
        e.g. dingir : AN --> dingir : A^^^^N """

        if len(string) == 1:
            """ Avoid dividing with zero """
            return [string] + [''] * longer
        
        out = [''] * longer
        shorter = len(string)
        for e, c in enumerate(string):
            out[e * (longer-1) // (shorter-1)] = c
        return out

    def chunk(string, shorter):
        """ Chunk target into multichar strings if source is
        shorter, e.g. AN : dingir --> AN : din^gir """
        
        string = list(tuple(target))
        k, m = divmod(len(string), shorter)
        return list(''.join(string[i*k+min(i, m):(i+1)*k+min(i+1, m)])
                 for i in range(shorter))

    strip_xlit = ''.join([c for c in xlit if c not in BRACKETS+'<>'+ignore])

    """ Ignore lines that have nothing to replace for efficiency """
    c = strip_xlit.count(source)
    if c == 0:
        return xlit

    """ Interpolate or chunk """
    if len(source) > len(target):
        target = interpolate(target, len(source))
    elif len(source) < len(target):
        target = chunk(target, len(source))
        if len(target) != len(source):
            print('Bad juju', source, target)
    else:
        target = list(tuple(target))
    source = list(tuple(source))

    """ Initialize trasducer """
    if word:
        parts = [tr.run(source, target, token, word) for token in tokenize(xlit)]
        return ' '.join(parts)
    else:
        return tr.run(source, target, xlit)
    
