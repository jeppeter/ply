#! /usr/bin/env python

import sys
import os
import importlib
import extargsparse
import logging
import json

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
from pygram import PythonCodeLex,make_flat_code
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


class FunctionLex(object):
    tokens = ['SEMI','LBRACE','RBRACE','COMMENT','TEXT']
    t_ignore = ''
    t_comment_ignore = ''
    states = (
        ('comment','exclusive'),
    )
    def __init__(self):
        self.lineno = 1
        self.column = 1
        self.linepos = 0
        self.braces = 0
        self.doublequoted = 0
        self.commented = 0
        return

    @lex.TOKEN(r'\#')
    def t_COMMENT(self,p):
        self.commented = 1
        p.lexer.push_state('comment')
        return None

    def t_comment_error(self,p):
        raise Exception('comment error')
        return

    @lex.TOKEN('.')
    def t_comment_TEXT(self,p):
        curpos = p.lexer.lexpos
        maxpos = len(p.lexer.lexdata)
        while curpos < maxpos:
            curch = p.lexer.lexdata[curpos]
            if curch == '\n':
                curpos += 1
                p.lexer.linepos = curpos
                break
            elif curch == ';':
                curpos += 1
                p.type = 'SEMI'
                p.value = ';'
                p.startline = p.lexer.lineno
                p.startpos = (curpos - p.lexer.linepos - len(p.value))
                p.endline = p.lexer.lineno
                p.endpos = (curpos - p.lexer.linepos)
                p.lexer.pop_state()
                p.lexer.lexpos = curpos
                return p
            curpos += 1
        self.comment = 0
        p.lexer.pop_state()
        p.lexer.lexpos = curpos
        return None


    def pass_double_quote(self,data,curpos,endpos):
        # included first 
        passed = 0
        slashed = False
        while curpos < endpos:
            curch = data[curpos]
            #logging.info('curch [%s]'%(curch))
            if slashed :
                slashed = False
            elif curch == '"':
                passed += 1
                break
            elif curch == '\\':
                slashed = True
            passed += 1
            curpos += 1
        #logging.info('passed %s'%(passed))
        return passed

    def pass_single_quote(self,data,curpos,endpos):
        # included first 
        passed = 0
        slashed = False
        while curpos < endpos:
            curch = data[curpos]
            #logging.info('curch [%s]'%(curch))
            if slashed :
                slashed = False
            elif curch == '\'':
                passed += 1
                break
            elif curch == '\\':
                slashed = True
            passed += 1
            curpos += 1
        #logging.info('passed %s'%(passed))
        return passed

    def set_text_value(self,p,passvalue,startline,endline,startpos,endpos,curpos):
        p.lexer.lexpos = curpos
        p.startline = startline
        p.endline = endline
        p.startpos = startpos
        p.endpos = endpos
        p.type = 'TEXT'
        p.value = passvalue
        return p


    @lex.TOKEN(r'.')
    def t_TEXT(self,p):
        startpos = p.lexer.lexpos - len(p.value)
        startline = p.lexer.lineno
        curpos = startpos
        endidx = len(p.lexer.lexdata)
        doublequoted = False
        singlequoted = False
        passvalue = ''
        startvalue = False
        endline = startline
        startpos = p.lexer.lineno - p.lexer.linepos - len(p.value)
        endpos = startpos
        while curpos < endidx:
            endpos = curpos - p.lexer.linepos
            curch = p.lexer.lexdata[curpos]
            #logging.info('[%d]curch %s'%(curpos,curch))
            if not startvalue:
                curpos += 1
                if curch == ' ' or curch =='\t':
                    pass
                elif curch == ';' or curch == '{' or curch == '}':
                    p.lexer.lexpos = curpos
                        #logging.info('curpos %s'%(curpos))
                    if curch == ';':
                        p.value = ';'
                        p.type = 'SEMI'
                    elif curch == '{':
                        p.value = '{'
                        p.type = 'LBRACE'
                    elif curch == '}':
                        p.value = '}'
                        p.type = 'RBRACE'
                    p.startline = p.lexer.lineno
                    p.endline = p.lexer.lineno
                    p.startpos = p.lexer.lexpos - p.lexer.linepos - len(p.value)
                    p.endpos = p.lexer.lexpos - p.lexer.linepos
                    #logging.info('p.lexer.lexpos [%s]'%(p.lexer.lexpos))
                    return p
                elif curch == '\#':
                    p.lexer.lexpos = curpos
                    p.lexer.push_state('comment')
                    return None
                else:
                    startvalue = True
                    passvalue = curch
            elif curch == '\'':
                curpos += 1
                passed = self.pass_single_quote(p.lexer.lexdata,curpos,endidx)
                passvalue += '\''
                passvalue += p.lexer.lexdata[curpos:(curpos+passed)]
                curpos += passed
                #logging.info('curpos %s [%s]'%(curpos,p.lexer.lexdata[curpos:]))
            elif curch == '"':
                curpos += 1
                passed = self.pass_double_quote(p.lexer.lexdata,curpos,endidx)
                passvalue += '"'
                passvalue += p.lexer.lexdata[curpos:(curpos + passed)]
                curpos += passed
            elif curch == '\n' :
                p.lexer.lineno += 1
                p.lexer.linepos = curpos
                curpos += 1
                return self.set_text_value(p,passvalue,startline,startpos,endline,endpos,curpos)
            elif curch == '\r':
                curpos += 1
            elif startvalue and  (curch == ';' or curch == '{' or curch == '}' or curch == '\#'):
                # we look for prev char
                #logging.info('curpos %s [%s]'%(curpos,curch))
                break
            else:
                passvalue += curch
                curpos += 1
        p.lexer.lexpos = curpos
        p.type = 'TEXT'
        p.value = passvalue
        p.startline = startline
        p.endline = p.lexer.lineno
        p.startpos = startpos - p.lexer.linepos
        p.endpos = curpos - p.lexer.linepos
        return p

    def t_error(self,p):
        self.column = p.lexpos = (p.lexer.lexpos - p.lexer.linepos )
        raise Exception('at [%s:%s] error [%s]'%(self.lineno,self.column,p.value))
        return

    def build(self,**kwargs):
        lexer = lex.lex(module=self,**kwargs)
        lexer.linepos = 0
        return lexer






class FunctionCode(object):
    def __init__(self,s,startpos,endpos):
        self.code= s
        self.startline = startpos.startline
        self.startpos = startpos.startpos
        self.endline = endpos.endline
        self.endpos = endpos.endpos
        return

    def location(self):
        s = '[%s:%s-%s:%s]'%(self.startline,self.startpos,self.endline,self.endpos)
        return s

    def format_self(self):
        s = ''
        s += '%s[%s]%s('%(self.location(),id(self),self.__class__.__name__)
        s += '%s'%(self.code)
        s += ')'
        return s

    def __str__(self):
        return self.format_self()

    def __repr__(self):
        return self.format_self()

class FunctionCodes(object):
    def __init__(self,tabs,startpos,endpos):
        self.curtab = tabs
        self.codes = []
        self.codetabs = []
        self.precodes = []
        self.precodetabs = []
        self.startline = startpos.startline
        self.startpos = startpos.startpos
        self.endline = endpos.endline
        self.endpos = endpos.endpos
        return

    def set_endpos(self,endpos):
        self.endline = endpos.endline
        self.endpos = endpos.endpos
        return

    def set_startpos(self,startpos):
        self.startline = startpos.startline
        self.startpos = startpos.startpos
        return

    def append_code(self,s):
        self.codes.append(s)
        self.codetabs.append(self.curtab)
        return

    def extend_codes(self,other):
        self.codes.extend(other.codes)
        self.codetabs.extend(other.codetabs)
        return


    def brace_code(self):
        idx = 0
        while idx < len(self.codetabs):
            self.codetabs[idx] += 1
            idx += 1
        return

    def __format_code(self,s,tabs=0):
        rets = ' ' * tabs * 4
        rets += s
        rets += '\n'
        return rets

    def format_code(self):
        idx = 0
        s = ''
        assert(len(self.codes) == len(self.codetabs))
        while idx < len(self.codes):
            #logging.info('tabs [%s]'%(self.codetabs[idx]))
            s += self.__format_code(self.codes[idx],self.codetabs[idx])
            idx += 1
        return s

    def location(self):
        s = '[%s:%s-%s:%s]'%(self.startline,self.startpos,self.endline,self.endpos)
        return s

    def format_self(self):
        s = ''
        s += '%s[%s]%s('%(self.location(),id(self),self.__class__.__name__)
        idx = 0
        while idx < len(self.codes):
            if idx > 0:
                s += ','
            s += '[%d][%s]'%(self.codetabs[idx],repr(self.codes[idx]))
            idx += 1
        s += ')'
        return s

    def __str__(self):
        return self.format_self()

    def __repr__(self):
        return self.format_self()


class FunctionYacc(object):
    tokens = FunctionLex.tokens
    def __init__(self,lexer=None,tabs=0):
        self.lexer = lexer
        self.statements = None
        self.tabs = tabs
        return

    def set_statements(self,p):
        self.statements = p
        return



    def p_statements_brace(self,p):
        ''' statements : statements lb_statements
        '''
        p[0] = p[1]
        logging.info('p1 [%s] p0 [%s] p2 [%s]'%(repr(p[1]),repr(p[0]),repr(p[2])))
        p[0].extend_codes(p[2])
        p[0].set_endpos(p[2])
        logging.info('extend_codes [%s] p2 [%s]'%(repr(p[0]),repr(p[2])))
        p[1] = None
        p[2] = None
        self.set_statements(p[0])
        return

    def p_statements_one(self,p):
        ''' statements : statements statement
        '''
        p[1].append_code(p[2].code)
        p[1].set_endpos(p[2])
        p[0] = p[1]
        logging.info('[%s]append [%s]'%(p[0],p[2]))
        p[1] = None
        p[2] = None
        self.set_statements(p[0])
        return



    def p_statements_empty(self,p):
        ''' statements : 
        '''
        startpos = location.Location()
        startpos.startline = p.lexer.lineno
        startpos.startpos = (p.lexer.lexpos-p.lexer.linepos)
        startpos.endline = startpos.startline
        startpos.endpos = startpos.startpos
        p[0] = FunctionCodes(self.tabs,startpos,startpos)
        startpos = None
        self.set_statements(p[0])
        logging.info('p0 [%s]'%(repr(p[0])))
        return

    def p_lb_statements(self,p):
        ''' lb_statements : LBRACE statements RBRACE
        '''
        p[0] = p[2]
        p[0].brace_code()
        p[0].set_startpos(p.slice[1])
        p[0].set_endpos(p.slice[3])
        logging.info('BRACE [%s]'%(repr(p[0])))
        p[2] = None
        return


    def p_statement_emtpy(self,p):
        ''' statement : SEMI
        '''
        p[0] = FunctionCode('')
        logging.info('code [%s]'%(p[0].code))
        return

    def p_statement_text(self,p):
        ''' statement : TEXT SEMI
        '''
        p[0] = FunctionCode(p.slice[1].value,p.slice[1],p.slice[2])
        logging.info('code [%s]'%(p[0]))
        return

    def p_error(self,p):
        raise Exception('can not handle %s'%(repr(p)))

    def build(self,**kwargs):
        return yacc.yacc(module=self,start='statements',**kwargs)


    def format_code(self):
        if self.statements is None:
            return ''
        return self.statements.format_code()


class Clause(object):
    def __init__(self,s,startpos,endpos):
        self.clause = s
        self.startline = startpos.startline
        self.startpos = startpos.startpos
        self.endline = endpos.endline
        self.endpos = endpos.endpos
        return


class Clauses(object):
    def __init__(self,prefix,startpos=None,endpos=None):
        self.prefix = prefix
        self.clauses = []
        self.startline = 1
        self.startpos = 1
        self.endline = 1
        self.endpos = 1
        if startpos is not None:
            self.startline = startpos.startline
            self.startpos = startpos.startpos
        if endpos is not None:
            self.endline = endpos.endline
            self.endpos = endpos.endpos
        return

    def set_startpos(self,startpos=None):
        if startpos is not None:
            self.startline = startpos.startline
            self.startpos = startpos.startpos
        return

    def set_endpos(self,endpos=None):
        if endpos is not None:
            self.endline = endpos.endline
            self.endpos = endpos.endpos
        return

    def append_clause(self,cls):
        self.clauses.append(cls.clause)
        return

    def __format_clause(self,s,tabs=0):
        rets = ' ' * tabs * 4
        rets += s
        rets += '\n'
        return rets

    def format_clause(self,tabs=0):
        idx = 0
        s = ''
        while idx < len(self.clauses):
            #logging.info('tabs [%s]'%(self.codetabs[idx]))
            curs = ''
            if idx == 0:
                curs += '\'\'\' %s : %s'%(self.prefix,self.clauses[idx])
            else:
                curs += '  | %s'%(self.clauses[idx])
            s += self.__format_clause(curs,tabs)
            idx += 1
        s += self.__format_clause('\'\'\'',tabs)
        return s

    def location(self):
        s = '[%s:%s-%s:%s]'%(self.startline,self.startpos,self.endline,self.endpos)
        return s

    def format_self(self):
        s = ''
        s += '%s[%s]%s('%(self.location(),id(self),self.__class__.__name__)
        s += '\n'
        s += self.format_clause(1)
        s += ')'
        return s

    def __str__(self):
        return self.format_self()

    def __repr__(self):
        return self.format_self()

class ClauseYacc(object):
    tokens = FunctionLex.tokens
    def __init__(self,lexer,prefix):
        self.prefix = prefix
        self.lexer = lexer
        self.statements = None
        return

    def set_statements(self,p):
        self.statements = p
        return


    def p_statements_state(self,p):
        ''' statements : statement
                    | statements statement 
        '''
        if len(p) == 2:
            p[0] = Clauses(self.prefix)
            p[0].append_clause(p[1])
            p[0].set_endpos(p[1])
            p[0].set_startpos(p[1])
            p[1] = None
        else:
            p[0] = p[1]
            p[0].append_clause(p[2])
            p[0].set_endpos(p[2])
            p[1] = None
            p[2] = None
        self.set_statements(p[0])
        return

    def p_statement(self,p):
        ''' statement : TEXT SEMI
        '''
        p[0] = Clause(p.slice[1].value,p.slice[1],p.slice[2])
        return

    def p_error(self,p):
        raise Exception('can not handle %s'%(repr(p)))


    def build(self,**kwargs):
        return yacc.yacc(module=self,start='statements',**kwargs)


    def format_clause(self,tabs):
        if self.statements is None:
            return ''
        return self.statements.format_clause(tabs)





def make_code(s,tabs):
    lexinput = FunctionLex()
    lexer = lexinput.build()
    yacchandle = FunctionYacc(lexer,tabs)
    parser = yacchandle.build(tabmodule='codeparse')
    parser.parse(s)
    rets = yacchandle.format_code()
    return rets

def make_clause(prefix,s,tabs):
    lexinput = FunctionLex()
    lexer = lexinput.build()
    yacchandle = ClauseYacc(lexer,prefix)
    parser = yacchandle.build(tabmodule='clauseparse')
    parser.parse(s)
    rets = yacchandle.format_clause(tabs)
    return rets

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
                    logging.info('')
                    prefix = normalize_name(v['prefix'])
                    curfuncname = 'p_%s_%s'%(normalize_name(k),funcidx)
                    rets += format_tabs('def %s(self,p):'%(curfuncname),tabs)
                    rets += make_clause(prefix,ya['clause'],(tabs+1))
                    rets += make_code(ya['func'],(tabs+1))
                funcidx += 1
    return rets

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
    rets = make_flat_code(s,args.tabwidth)
    write_file(rets,args.output)
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
        }
    }
    '''
    parser = extargsparse.ExtArgsParse()
    parser.load_command_line_string(command)
    args = parser.parse_command_line()
    return

if __name__ == '__main__':
    main()
