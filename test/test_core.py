# -*- Mode: Python -*-

# parse the test cases from bitcoin-core

import os
import json

from caesure.script import *
from caesure.bitcoin import TX, ZERO_NAME, KEY

def frob (s):
    # the test files are illegal json.  escape all the newlines in strings.
    state_string = False
    r = []
    for i in range (len (s)):
        ch = s[i]
        if state_string:
            if ch == '\n':
                ch = r'\u000a'
            elif ch == '"':
                state_string = False
            r.append (ch)
        else:
            if ch == '"':
                state_string = True
            r.append (ch)
    return ''.join (r)

where = '/Users/rushing/src/bitcoin/src/test/data/'

valid   = json.loads (frob (open (os.path.join (where, 'script_valid.json'), 'rb').read()))
invalid = json.loads (frob (open (os.path.join (where, 'script_invalid.json'), 'rb').read()))

import re
digits = re.compile ('-?[0-9]+$')

def parse_test (s):
    r = []
    for e in s.split():
        if digits.match (e):
            # push this integer
            r.append (make_push_int (int (e)))
        elif e.startswith ('0x'):
            # add raw hex to the script
            r.append (e[2:].decode ('hex'))
        elif len(e) >= 2 and e[0] == "'" and e[-1] == "'":
            # add a push to the script
            r.append (make_push_str (e[1:-1]))
        elif opcode_map_fwd.has_key (e):
            r.append (chr(opcode_map_fwd[e]))
        elif opcode_map_fwd.has_key ('OP_'+e):
            r.append (chr(opcode_map_fwd['OP_'+e]))
        else:
            raise ValueError ("i'm so conFUSEd")
    return ''.join (r)

import sys
W = sys.stderr.write

def do_one (unlock_script, lock_script, flags):
    #W (('-' *50)+'\n')

    tx0 = TX()
    tx0.inputs = [((ZERO_NAME, 4294967295), '\x00\x00', 4294967295)]
    tx0.outputs = [(0, lock_script)]
    name = tx0.get_hash()
    tx1 = TX()
    tx1.inputs = [((name, 0), unlock_script, 4294967295)]
    tx1.outputs = [(0, '')]

    if 'P2SH' in flags:
        m = verifying_machine_p2sh (tx1, 0, KEY)
    else:
        m = verifying_machine (tx1, 0, KEY)
    m.strictenc = 'STRICTENC' in flags
    m.minimal = 'MINIMALDATA' in flags
    m.nulldummy = 'NULLDUMMY' in flags
    m.dersig = 'DERSIG' in flags
    m.low_s = 'LOW_S' in flags
    m.sigpushonly = 'SIGPUSHONLY' in flags
    m.eval_script (unlock_script, lock_script)

def unit_tests():
    W ('%d valid tests...\n' % (len(valid),))
    fails = []
    for i, v in enumerate (valid):
        v = [bytes(x) for x in v]
        if len(v) >= 2:
            flags = v[2].split(',')
            unlock = parse_test (v[0])
            lock = parse_test (v[1])
            #print i, v
            #print pprint_script (parse_script (unlock))
            #print pprint_script (parse_script (lock))
            try:
                do_one (unlock, lock, flags)
            except Exception as e:
                fails.append ((i, 'valid', v, e))
    W ('%d invalid tests...\n' % (len(invalid),))
    for i, v in enumerate (invalid):
        v = [bytes(x) for x in v]
        if len(v) >= 2:
            flags = v[2].split(',')
            try:
                unlock = parse_test (v[0])
                lock = parse_test (v[1])
                #print i, v
                #print pprint_script (parse_script (unlock))
                #print pprint_script (parse_script (lock))
                do_one (unlock, lock, flags)
                fails.append ((i, 'invalid', v, None))
            except:
                pass
    if fails:
        W ('%d failures:\n' % (len(fails)))
        for i, kind, fail, why in fails:
            W ('  %d %s %r, %r\n' % (i, kind, fail, why))

def pprint_unit_tests():
    for v in valid:
        sig, pub = v[:2]
        sig0 = parse_script (sig)
        pub0 = parse_script (pub)
        W ('%r\n%r\n' % (sig0, pub0))
        W ('%r\n%r\n' % (pprint_script (sig0), pprint_script (pub0)))
        W ('-----------\n')

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser (description='run bitcoin-core unit script tests')
    p.add_argument ('-v', type=int, action='append', help='run a specific valid test by number')
    p.add_argument ('-i', type=int, action='append', help='run a specific invalid test by number')
    p.add_argument ('-d', action='store_true', help='debug')
    args = p.parse_args()

    if args.v is not None:
        tests = []
        for num in args.v:
            tests.append (valid[num])
        valid = tests
        invalid = []

    if args.i is not None:
        tests = []
        for num in args.i:
            tests.append (invalid[num])
        invalid = tests
        valid = []

    if args.d:
        verifying_machine.debug = True
        
    unit_tests()
    #pprint_unit_tests()
