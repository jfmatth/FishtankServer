
'''
    Module benc: As per bittorrent spec: http://www.bittorrent.org/protocol.html
'''

def decode(s):
    try:
        struct,  s = _eat_any(s)
    except:
        raise ValueError("Invalid bencoded string")
    if len(s):
        raise ValueError("Invalid bencoded string, junk data at '%s'" % s)
    else:
        return struct

def decode_file(s):
    return decode(open(s).read().strip())

def _eat_any(s):
    ''' s might be a string,  int,  dict,  or list, so use the appropriate method.  Returns (parsed_data, leftovers) '''
    cmds = {'i': _eat_int,  'l': _eat_list, 'd':_eat_dict}
    try:
        return cmds[s[0]](s[1:])
    except:
        #strings have no magical character that delimits them, just a length prefix
        return _eat_str(s)

def _eat_str(s):
    ''' s is length-prefixed '''
    head, tail = s.split(':',  1)
    strlen = int(head)
    return (tail[:strlen], tail[strlen:])

def _eat_int(s):
    ''' format: i42e '''
    head,  tail = s.split('e',  1)
    return (int(head), tail)

def _eat_list(s):
    ''' Format: l(many values)e'''
    r = []
    while s[0] is not 'e':
        cur_result,  s = _eat_any(s)
        r.append(cur_result)
    return (r,  s[1:])

def _eat_dict(s):
    ''' Format: d(many values)e.  Keys must be strings.
       Actual parsing is done by _eat_list; dict turns them into pairs '''
    d, s = _eat_list(s)
    d = dict(zip(d[::2], d[1::2]))
    return (d, s)

def encode(struct):
    return {
        int: _enc_int, 
        long: _enc_int, 
        str: _enc_str, 
        list: _enc_list, 
        dict: _enc_dict
    }.get(type(struct), lambda x: None)(struct)
    
def _enc_str(s):
    return '%i:%s' % (len(s),  s)

def _enc_int(i):
    return 'i%ie' % i

def _enc_list(l):
    return 'l%se' % ''.join(map(encode, l))

def _enc_dict(d):
    pairs = d.items()
    pairs.sort()
    return 'd%se' % ''.join(encode(str(i[0])) + encode(i[1]) for i in pairs)

if __name__ == '__main__':
    print 'Main module.  Testing commencing'
    d = {'1':2, 3:[4, '5']}
    print d
    print 'encoding'
    s = encode(d)
    print s
    print 'decoding'
    print decode(s)
