#! /usr/bin/env python

import sys
import os
import importlib
import extargsparse
import logging
import json
import unittest
import re
import imp
import inspect

def _insert_path(path,*args):
    _curdir = os.path.join(path,*args)
    if _curdir  in sys.path:
        sys.path.remove(_curdir)
    sys.path.insert(0,_curdir)
    return

_insert_path(os.path.dirname(os.path.realpath(__file__)))
_insert_path(os.path.dirname(os.path.realpath(__file__)),'..','..')

import ply.lex as lex
import ply.yacc as yacc
from funcgram import FunctionLex,make_code
from clausegram import make_clause
from pygram import PythonCodeLex,make_flat_code
from pyclausegram import PyClauseLex,make_pyclause
import location

class Utf8Encode(object):
    def __dict_utf8(self,val):
        newdict =dict()
        for k in val.keys():
            newk = self.__encode_utf8(k)
            newv = self.__encode_utf8(val[k])
            newdict[newk] = newv
        return newdict

    def __list_utf8(self,val):
        newlist = []
        for k in val:
            newk = self.__encode_utf8(k)
            newlist.append(newk)
        return newlist

    def __encode_utf8(self,val):
        retval = val

        if sys.version[0]=='2' and isinstance(val,unicode):
            retval = val.encode('utf8')
        elif isinstance(val,dict):
            retval = self.__dict_utf8(val)
        elif isinstance(val,list):
            retval = self.__list_utf8(val)
        return retval

    def __init__(self,val):
        self.__val = self.__encode_utf8(val)
        return

    def __str__(self):
        return self.__val

    def __repr__(self):
        return self.__val
    def get_val(self):
        return self.__val



def read_file(infile=None):
    fin = sys.stdin
    if infile is not None:
        logging.info('infile %s'%(infile))
        fin = open(infile,'r')
    bmode = False
    if 'b' in fin.mode:
        bmode = True
    s = ''
    for l in fin:
        if sys.version[0] == '2' or not bmode:
            s += l
        else:
            s += l.decode(encoding='UTF-8')
    if fin != sys.stdin:
        fin.close()
    fin = None
    return s

def write_file(s,outfile=None):
    fout = sys.stdout
    if outfile is not None:
        fout = open(outfile,'wb')
    bmode = False
    if 'b' in fout.mode:
        bmode = True
    if sys.version[1] == '2' or not bmode:
        fout.write('%s'%(s))
    else:
        fout.write(s.encode(encoding='UTF-8'))
    if fout != sys.stdout:
        fout.close()
    fout = None
    return

class debug_makecode_case(unittest.TestCase):
    def setUp(self):
        return

    def tearDown(self):
        return

    @classmethod
    def setupClass(cls):
        return

    @classmethod
    def tearDownClass(cls):
        return

    def py_encode_test(self,instr,tabs=0,deftabwidth=4):
        insarr = []
        for l in re.split('\n',instr):
            l = l.rstrip('\r\n')
            if len(l) == 0:
                continue
            insarr.append(l.rstrip('\r\n'))
        outc = make_flat_code(instr,deftabwidth,False)
        outs = make_code(outc,tabs)
        outsarr = []
        for l in re.split('\n',outs):
            l = l.rstrip('\r\n')
            if len(l) == 0:
                continue
            outsarr.append(l)

        self.assertEqual(len(insarr),len(outsarr))
        for idx in range(len(outsarr)):
            self.assertEqual(insarr[idx],outsarr[idx])
        return

    def pyclause_encode_test(self,instr,outstr,tabs=0):
        outs = make_pyclause(instr,tabs)
        outsarr = []
        for l in re.split('\n',outs):
            l = l.rstrip('\n\r')
            outsarr.append(l)
        valsarr = []
        for l in re.split('\n',outstr):
            l = l.rstrip('\r\n')
            valsarr.append(l)
        self.assertEqual(len(outsarr),len(valsarr))
        idx = 0
        while idx < len(valsarr):
            self.assertEqual(outsarr[idx],valsarr[idx])
            idx += 1
        return

    def test_A001(self):
        instr='''        if len(p) == 2:
            p[0] = dhcpconf.DomainList()
            p[0].append_child_and_set_pos(p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[3])
            p[1] = None
            p[2] = None
        return'''
        self.py_encode_test(instr,2,4)
        return

    def test_B001(self):
        instr=''' statement :  option_statement
                  | execute_statement
                  | subnet_statement
                  | host_statement
        '''
        self.pyclause_encode_test(instr,' option_statement; execute_statement; subnet_statement; host_statement;')
        return



def load_config(infile=None):
    retobj = dict()
    try:
        fin = sys.stdin
        if infile is not None:
            fin = open(infile,'r')
        retobj = json.load(fin)
        retobj = Utf8Encode(retobj).get_val()
    except:
        logging.error('can not handle [%s] for json'%(infile))
        retobj = dict()
    return retobj



def set_logging(args):
    loglvl= logging.ERROR
    if args.verbose >= 3:
        loglvl = logging.DEBUG
    elif args.verbose >= 2:
        loglvl = logging.INFO
    if logging.root is not None and len(logging.root.handlers) > 0:
        logging.root.handlers = []
    logging.basicConfig(level=loglvl,format='%(asctime)s:%(filename)s:%(funcName)s:%(lineno)d\t%(message)s')
    return

def lex_handler(args,parser):
    set_logging(args)
    s = read_file(args.input)
    lexinput = FunctionLex()
    lexer = lexinput.build()
    lexer.input(s)
    while True:
        tok = lexer.token()
        if tok is None:
            break
        sys.stdout.write('(%s,%r,%d,%d)\n' % (tok.type, tok.value, tok.startline, tok.startpos))
    sys.exit(0)
    return


def yacc_handler(args,parser):
    set_logging(args)
    s = read_file(args.input)
    rets = make_code(s,args.tabs)
    sys.stdout.write('%s'%(rets))
    sys.exit(0)
    return

def clause_handler(args,parser):
    set_logging(args)
    s = read_file(args.input)
    rets = make_clause(args.prefix,s,args.tabs)
    sys.stdout.write('%s'%(rets))
    sys.exit(0)
    return

def format_tabs(s,tabs=0):
    rets = ' ' * tabs * 4
    rets += s
    rets += '\n'
    return rets

def isdict(v):
    if v is not None and isinstance(v,dict):
        return True
    return False

def haskey(v,k):
    if not isdict(v):
        return False
    if k in v.keys():
        return True
    return False

def islist(v):
    if v is not None and (isinstance(v,list) or  isinstance(v,tuple)):
        return True
    return False

def normalize_name(n):
    retn = n
    if not isinstance(n,str):
        raise Exception('%s not string'%(n))
    retn = retn.replace('-','_')
    retn = retn.lower()
    return retn

def output_p(k,v,tabs):
    rets = ''
    logging.info('')
    if haskey(v,'yacc'):
        # this need to output
        yv = v['yacc']
        logging.info('')
        if islist(yv):
            logging.info('')
            funcidx = 0
            for ya in yv:
                logging.info('')
                if haskey(ya,'clause') and haskey(ya,'func') and haskey(v,'prefix'):
                    if k != v['prefix']:
                        logging.error('%s not equal [%s]'%(k,v['prefix']))
                    logging.info('')
                    prefix = normalize_name(v['prefix'])
                    curfuncname = 'p_%s_%s'%(normalize_name(k),funcidx)
                    rets += format_tabs('def %s(self,p):'%(curfuncname),tabs)
                    logging.info('make [%s] [%s]'%(k,ya['clause']))
                    rets += make_clause(prefix,ya['clause'],(tabs+1))
                    rets += make_code(ya['func'],(tabs+1))
                funcidx += 1
    return rets

def make_special_identifier(odict,okeys,tabs):
    s = ''

    s += format_tabs('def p_special_identifier_0(self,p):',tabs)
    s += ' ' * (tabs+1) * 4
    s += '\'\'\' special_identifier : '
    idx = 0
    for k in okeys:
        v = odict[k]
        if isinstance(v,dict):
            continue
        if idx > 0:
            s += format_tabs('  | %s'%(v),(tabs+1))
        else:
            s += '%s\n'%(v)
        idx += 1
    s += format_tabs('\'\'\'',tabs+1)
    s += format_tabs('p[0] = dhcpconf.ConstData(p.slice[1].value,p.slice[1],p.slice[1])',(tabs+1))
    s += format_tabs('return',(tabs+1))            
    return s

def yclass_handler(args,parser):
    set_logging(args)
    odict = load_config(args.input)
    okeys = sorted(odict.keys())
    outs = ''
    outs += format_tabs('class %s(object):'%(args.classname),0)
    outs += format_tabs('def __init__(self,lexer=None):',1)
    outs += format_tabs('self.lexer = lexer',2)
    outs += format_tabs('self.statements = None',2)
    outs += format_tabs('return',2)
    outs += format_tabs('',2)
    logging.info('okeys %s'%(repr(okeys)))
    for k in okeys:
        v = odict[k]
        if isdict(v):
            outs += output_p(k,v,1)
            outs += format_tabs('',1)
    outs += make_special_identifier(odict,okeys,1)

    ins = read_file(args.subnargs[0])
    if args.pattern is None:
        args.pattern = 'class %s(object):pass'%(args.classname)
    repls = ins.replace(args.pattern,outs)
    write_file(repls,args.subnargs[1])    
    sys.exit(0)
    return

def lclass_handler(args,parser):
    set_logging(args)
    odict = load_config(args.input)
    okeys = sorted(odict.keys())
    kv = dict()
    for k in okeys:
        v = odict[k]
        if isdict(v):
            if haskey(v,'value'):
                kv[k] = v['value']
        else:
            kv[k] = v
    outs = ''
    outs += format_tabs('class %s(object):'%(args.classname),0)
    outs += format_tabs('reserved = {',1)
    idx = 0
    klen = len(kv.keys())
    for k in kv.keys():
        curs = '\'%s\' : \'%s\''%(k,kv[k])
        if idx < (klen - 1):
            curs += ','
        outs += format_tabs(curs,2)
        idx += 1            
    outs += format_tabs('}',1)
    outs += format_tabs('def __init__(self):',1)
    outs += format_tabs('return',2)
    outs += format_tabs('',2)
    ins = read_file(args.subnargs[0])
    if args.pattern is None:
        args.pattern = 'class %s(object):pass'%(args.classname)
    repls = ins.replace(args.pattern,outs)
    write_file(repls,args.subnargs[1])    
    sys.exit(0)
    return

def pylex_handler(args,parser):
    set_logging(args)
    s = read_file(args.input)
    lexinput = PythonCodeLex()
    lexer = lexinput.build()
    lexer.input(s)
    while True:
        tok = lexer.token()
        if tok is None:
            break
        sys.stdout.write('[%d](%s,%r,%d,%d)\n' % (tok.lexer.lastspace,tok.type, tok.value, tok.startline, tok.startpos))
    sys.exit(0)
    return

    sys.exit(0)
    return

def pyyacc_handler(args,parser):
    set_logging(args)
    s = read_file(args.input)
    rets = make_flat_code(s,args.tabwidth,args.usequoted)
    write_file(rets,args.output)
    sys.exit(0)
    return

def pyclauselex_handler(args,parser):
    set_logging(args)
    s = read_file(args.input)
    lexinput = PyClauseLex()
    lexer = lexinput.build()
    lexer.input(s)
    while True:
        tok = lexer.token()
        if tok is None:
            break
        sys.stdout.write('(%s,%r,%d,%d)\n' % (tok.type, tok.value, tok.startline, tok.startpos))   
    sys.exit(0)
    return

def pyclauseyacc_handler(args,parser):
    set_logging(args)
    s = read_file(args.input)
    rets = make_pyclause(s,args.tabs)
    write_file(rets,args.output)
    sys.exit(0)
    return


def test_handler(args,parser):
    set_logging(args)
    sys.argv[1:]=args.subnargs
    unittest.main(verbosity=args.verbose,failfast=args.failfast)
    sys.exit(0)
    return

class OutDict(object):
    def __init__(self,m):
        self.__mod = m
        self.odict = dict()
        return

    def __get_class(self,name):
        cls = getattr(self.__mod,name,None)
        if cls is None:
            raise Exception('%s not class'%(name))
        if not inspect.isclass(cls):
            raise Exception('%s not class'%(name))
        return cls

    def __get_meth(self,cls,funcname):
        func = getattr(cls,funcname,None)
        if func is None:
            raise Exception('can not get %s'%(funcname))
        if not inspect.ismethod(func):
            raise Exception('not method %s'%(funcname))
        return func


    def add_odict(self,optname,docstr,codestr):
        docjson = make_pyclause(docstr,0)
        codejson = make_flat_code(codestr,4,False)
        if optname in self.odict.keys():
            v = self.odict[optname]
        else:
            v = dict()
            v['prefix'] = optname
            v['yacc'] = []
        appv = dict()
        appv['clause'] = docjson
        appv['func'] = codejson
        v['yacc'].append(appv)
        self.odict[optname] = v
        return

    def add_class(self,name):
        cls = self.__get_class(name)
        nameexpr = re.compile('^p_([0-9a-zA-Z_]+)_([\d]+)$')
        tripexpr = re.compile('^\s+\'\'\'.*')
        for k in dir(cls):
            m = nameexpr.findall(k)
            if m is not None and len(m) > 0 and len(m[0]) >= 2:
                optname = m[0][0]
                optidx = m[0][1]                
                func = getattr(cls,k,None)
                if func is not None and inspect.isfunction(func):
                    docstr = inspect.getdoc(func)
                    codearr,_ = inspect.getsourcelines(func)
                    codestr = ''
                    idx = 0
                    docstarted = False
                    for l in codearr:
                        if idx > 0:
                            if docstarted:
                                if tripexpr.match(l):
                                    docstarted = False
                                    logging.info('revert %s'%(l))
                            else:
                                if tripexpr.match(l):
                                    docstarted = True
                                    logging.info('l %s matched doc'%(l))
                                if not docstarted:
                                    codestr += l
                        idx += 1
                    logging.info('doc %s \ncodestr\n%s'%(docstr,codestr))
                    self.add_odict(optname,docstr,codestr)
        return

    def format_json(self):
        s = json.dumps(self.odict,indent=4)
        logging.info('%s'%(s))
        return s

    def add_function(self,name):
        sarr = re.split('\.',name)
        if len(sarr) < 2:
            raise Exception('%s not valid method'%(name))
        cls = self.__get_class(sarr[0])
        meth = self.__get_meth(cls,sarr[1])
        return


def tojson_handler(args,parser):
    set_logging(args)
    if args.input is None:
        raise Exception('need -i|--input file')
    m = imp.load_source('outer',args.input)
    odict = OutDict(m)
    for c in args.subnargs:
        if '.' in c:
            # now we should get
            odict.add_function(c)
        else:
            odict.add_class(c)
    s = odict.format_json()
    write_file(s,args.output)
    sys.exit(0)
    return

def main():
    command='''
    {
        "verbose|v" : "+",
        "input|i" : null,
        "output|o" : null,
        "tabs|t" : 0,
        "tabwidth|w" : 4,
        "classname|c" : "ExtendedYacc",
        "prefix|p" : "statements",
        "pattern|P"  : null,
        "usequoted|u" : true,
        "failfast|f" : true,
        "lex<lex_handler>" : {
            "$" : 0
        },
        "yacc<yacc_handler>" : {
            "$" : 0
        },
        "clause<clause_handler>" : {
            "$" : 0
        },
        "yclass<yclass_handler>##input[0] templatefile input[1] outputfile##" : {
            "$" : 2
        },
        "lclass<lclass_handler>##input[0] templatefile input[1] outputfile##" : {
            "$" : 2
        },
        "pylex<pylex_handler>" : {
            "$" : 0
        },
        "pyyacc<pyyacc_handler>" : {
            "$" : 0
        },
        "pyclauselex<pyclauselex_handler>" : {
            "$" : 0
        },
        "pyclauseyacc<pyclauseyacc_handler>" : {
            "$" : 0
        },
        "tojson<tojson_handler>" : {
            "$" : "+"
        },
        "test<test_handler>" : {
            "$" : "*"
        }
    }
    '''
    argparser = extargsparse.ExtArgsParse()
    argparser.load_command_line_string(command)
    args = argparser.parse_command_line()
    return

if __name__ == '__main__':
    main()
