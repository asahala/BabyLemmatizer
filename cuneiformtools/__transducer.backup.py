

    s_ = source.copy()
    t_ = target.copy()

    """ Transducer for doing the replacements """
    output_tape = []
    tmp_out_tape = {'orig': [], 'trans': []}
    scan_pos = 0

    for c in xlit:

        if c in BRACKETS + ignore:
            tmp_out_tape['orig'].append(c)
            tmp_out_tape['trans'].append(c)
            continue
        
        # do not transduce
        tmp_out_tape['orig'].append(c)

        if c == s_[0]:
            # transduce
            c_orig = c
            c_trans = t_.pop(0)
            s_.pop(0)
            tmp_out_tape['trans'].append(c_trans)
            #print(c_orig, c_trans, 'tra', tmp_out_tape, sep='\t')
        else:# c != s_[0]:
            # reject output tape
            #print(c, c, 'rej', tmp_out_tape, sep='\t')
            output_tape += tmp_out_tape['orig']
            tmp_out_tape['trans'] = []
            tmp_out_tape['orig'] = []
            s_ = source.copy()
            t_ = target.copy()

        if not s_:
            # accept output tape
            output_tape += tmp_out_tape['trans']
            tmp_out_tape['trans'] = []
            tmp_out_tape['orig'] = []
            s_ = source.copy()
            t_ = target.copy()
    return ''.join(output_tape)

    
    """
    signs, delimiters = unzip_xlit(line, extra_delimiters=' ')
    o = zip_xlit(signs, delimiters)

    def repl(sign):
        b_indices = {}
        for s, t in replacements:
            if sign == s:
                return t
            for e, c in enumerate(sign):
                if c in BRACKETS:
                    if e == len(sign)-1:
                        e = -1
                    b_indices[c] = e
            print(b_indices, sign)
                
            

    #signs = [repl(s) for s in signs]     """ 
    









        """
        output_tape = re.sub(re.compile('(.)(\[|⸢)(\]|⸣)'), r'\2\1\3', output_tape)
        output_tape = re.sub('([%s])(\]|⸣)' % re.escape(DELIMITERS), r'\2\1', output_tape)
        output_tape = re.sub('(\[|⸢)(})', r'\2\1', output_tape)
        output_tape = re.sub('([%s])(\w+?)([%s])' % (re.escape(self.ignore), re.escape(DELIMITERS + ' ')), r'\2\1\3', output_tape)
        """
        
        print('===================================================')
        print('   INPUT: ', xlit, sep='\t')
        print('   OUTPUT:', output_tape.replace('§', ''), sep='\t')
        print('===================================================')
        print('\n')

        

        """ Attempt to fix possible errors """
        o_bracket_flags = list(get_bracket_flags(output_tape))
        bracket_flags = list(get_bracket_flags(xlit))

        """ Flip obvious mistakes such as an-] --> an]- or x[] -> [x] """
        output_tape = re.sub('(.)(\[|⸢)(\]|⸣)', r'\2\1\3', output_tape)
        output_tape = re.sub('([%s])(\]|⸣)' % re.escape(DELIMITERS), r'\2\1', output_tape)
        
        """ Check if bracket contexts have changed """
        if bracket_flags == o_bracket_flags:
            return output_tape.replace(self.boundary, '')
        else:
            """ If positions have changed, rearrange """
            signs, delimiters = unzip_xlit(output_tape, extra_delimiters=' ')
            new_signs = []

            for se, sign in enumerate(signs):
                new_sign = []
                stack = ''
                for e, c in enumerate(sign):
                    """ If bracket, see desired position and insert to
                    beginning or add to append stack """
                    if c in BRACKETS:
                        pos = bracket_flags.pop(0)
                        if pos == -1:
                            stack += c
                            continue
                        elif pos == 0:
                            new_sign.insert(0, c)
                            continue
                    elif c in self.ignore:
                        """ If ignored symbol is found in the beginning
                        (they should be final), move to the end of the
                        previous sign """
                        if e == 0:
                            new_signs[se-1] += c
                        else:
                            stack += c
                        continue

                    new_sign.append(c)
                new_sign.append(stack)
                new_signs.append(''.join(new_sign))

            return zip_xlit(new_signs, delimiters)
