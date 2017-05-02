#! /usr/bin/env python

import sys
import os
import logging

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
import location

class PyClauseArgs(location.Location):
    def __init__(self,startelm=None,endelm=None):
        startline = 1
        startpos = 1
        endline = 1
        endpos = 1
        if startelm is not None:
            startline = startelm.startline
            startpos = startelm.startpos
        if endelm is not None:
            endline = endelm.endline
            endpos = endelm.endpos
        super(PyClauseArgs,self).__init__(startline,startpos,endline,endpos)
        self.values = []
        return

    def append_args(self,value):
        self.values.append(value)
        return

class PyClauseList(location.Location):
    def __init__(self,startelm=None,endelm=None):
        startline = 1
        startpos = 1
        endline = 1
        endpos = 1
        if startelm is not None:
            startline = startelm.startline
            startpos = startelm.startpos
        if endelm is not None:
            endline = endelm.endline
            endpos = endelm.endpos
        super(PyClauseList,self).__init__(startline,startpos,endline,endpos)
        self.args = []
        return

    def append_args(self,args):
        if args is not None :
            if issubclass(args.__class__,PyClauseArgs):
                clauseargs = []
                for c in args.values:
                    clauseargs.append(c)
                self.args.append(clauseargs)
            else:
                logging.error('not PyClauseArgs')
        return


class PyClause(location.Location):
    def __init__(self,name,startelm=None,endelm=None):
        startline = 1
        startpos = 1
        endline = 1
        endpos = 1
        if startelm is not None:
            startline = startelm.startline
            startpos = startelm.startpos
        if endelm is not None:
            endline = endelm.endline
            endpos = endelm.endpos
        super(PyClause,self).__init__(startline,startpos,endline,endpos)
        self.args = []
        self.name = name
        return

    def extend_children(self,args):
        if args is not None :
            assert(self.name is not None)
            if issubclass(args.__class__,PyClauseList):
                self.args = args.args
            else:
                logging.error('not PyClauseList')
        return

    def format_clause(self,tabs):
        s = ''
        if self.name is not None:
            idx = 0
            for c in self.args:
                for k in c:
                    s += ' %s'%(k)
                s += ';'
        return s

class PyClauses(location.Location):
    def __init__(self,startelm=None,endelm=None):
        startline = 1
        startpos = 1
        endline = 1
        endpos = 1
        if startelm is not None:
            startline = startelm.startline
            startpos = startelm.startpos
        if endelm is not None:
            endline = endelm.endline
            endpos = endelm.endpos
        super(PyClauses,self).__init__(startline,startpos,endline,endpos)
        self.clauses = []
        return

    def append_clause(self,cls):
        if cls is not None:
            if issubclass(cls.__class__,PyClause):
                if cls.name is not None:
                    self.clauses.append(cls)
            else:
                logging.error('not PyClase class')
        return

    def format_clause(self,tabs=0):
        s = ''
        idx = 0
        for c in self.clauses:
            if idx > 0:
                s += '\n'
            s += c.format_clause(tabs)
            idx += 1
        return s



class PyClauseLex(object):
    tokens = ['TRI_SQUOTE','TRI_DQUOTE','TEXT','COLON','PIPE']
    t_ignore = ' \t'
    def __init__(self):
        self.lineno = 1
        self.linepos = 0
        return

    @lex.TOKEN(r'\n')
    def t_newline(self,p):
        self.lineno += 1
        self.linepos = p.lexer.lexpos
        p.lexer.lineno += 1
        p.lexer.linepos = p.lexer.lexpos
        return None

    @lex.TOKEN(r'\r')
    def t_carriage(self,p):
        return None


    @lex.TOKEN(r'[a-z0-9A-Z_]+')
    def t_TEXT(self,p):
        p.startpos = p.lexer.lexpos -  self.linepos  - len(p.value)
        p.startline = self.lineno
        p.endline = self.lineno
        p.endpos = p.lexer.lexpos -  self.linepos
        return p

    @lex.TOKEN(r'\:')
    def t_COLON(self,p):
        p.startpos = p.lexer.lexpos -  self.linepos  - len(p.value)
        p.startline = self.lineno
        p.endline = self.lineno
        p.endpos = p.lexer.lexpos -  self.linepos
        return p

    @lex.TOKEN(r'\|')
    def t_PIPE(self,p):
        p.startpos = p.lexer.lexpos -  self.linepos  - len(p.value)
        p.startline = self.lineno
        p.endline = self.lineno
        p.endpos = p.lexer.lexpos -  self.linepos
        return p

    @lex.TOKEN(r'\'\'\'')
    def t_TRI_SQUOTE(self,p):
        p.startpos = p.lexer.lexpos -  self.linepos  - len(p.value)
        p.startline = self.lineno
        p.endline = self.lineno
        p.endpos = p.lexer.lexpos -  self.linepos
        return p

    @lex.TOKEN(r'"""')
    def t_TRI_DQUOTE(self,p):
        p.startpos = p.lexer.lexpos -  self.linepos  - len(p.value)
        p.startline = self.lineno
        p.endline = self.lineno
        p.endpos = p.lexer.lexpos -  self.linepos
        return p


    def t_error(self,p):
        self.column = (p.lexer.lexpos - self.linepos )
        raise Exception('at [%s:%s] error [%s]'%(self.lineno,self.column,p.value))
        return

    def build(self,**kwargs):
        lexer = lex.lex(module=self,**kwargs)
        lexer.lineno = 1
        lexer.linepos = 0
        return lexer

class PyClauseYacc(object):
    tokens = PyClauseLex.tokens
    def __init__(self):
        self.statements = None
        return

    def set_statements(self,p):
        self.statements = p
        return


    def p_statements_0(self,p):
        ''' statements : statement
                    | statements statement 
        '''
        if len(p) == 2:
            p[0] = PyClauses()
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

    def p_statements_1(self,p):
        ''' statements : 
        '''
        startpos = location.Location()
        startpos.startline = p.lexer.lineno
        startpos.startpos = (p.lexer.lexpos-p.lexer.linepos)
        startpos.endline = startpos.startline
        startpos.endpos = startpos.startpos
        p[0] = PyClauses(startpos,startpos)
        startpos = None
        self.set_statements(p[0])
        #logging.info('p0 [%s]'%(repr(p[0])))
        return


    def p_statement_0(self,p):
        ''' statement : TRI_SQUOTE inner_statement TRI_SQUOTE
                 | TRI_DQUOTE inner_statement TRI_DQUOTE
        '''
        p[0] = p[2]
        p[0].set_startpos(p.slice[1])
        p[0].set_endpos(p.slice[3])
        p[2] = None
        return


    def p_statement_1(self,p):
        ''' statement : TRI_SQUOTE TRI_SQUOTE
               | TRI_DQUOTE TRI_DQUOTE
        '''
        p[0] = PyClause(None,p.slice[1],p.slice[2])
        return

    def p_statement_2(self,p):
        ''' statement : inner_statement
        '''
        p[0] = p[1]
        p[1] = None
        return

    def p_inner_statement_0(self,p):
        ''' inner_statement : TEXT COLON inner_statement_list
        '''
        p[0] = PyClause(p.slice[1].value,p.slice[1],p[3])
        p[0].extend_children(p[3])
        p[3] = None
        return

    def p_innsert_statement_list_0(self,p):
        ''' inner_statement_list : inner_statement_args 
                    | inner_statement_list PIPE inner_statement_args
        '''
        if len(p) == 2:
            p[0] = PyClauseList(p[1],p[1])
            p[0].append_args(p[1])
            p[1] = None
        elif len(p) == 4:
            p[0]= p[1]
            p[0].append_args(p[3])
            p[0].set_endpos(p[3])
            p[1] = None
            p[3] = None
        else:
            raise Exception('can not handle %s'%(repr(p)))
        return

    def p_innert_statement_args_0(self,p):
        ''' inner_statement_args :                 
        '''
        startpos = location.Location()
        startpos.startline = p.lexer.lineno
        startpos.startpos = (p.lexer.lexpos-p.lexer.linepos)
        startpos.endline = startpos.startline
        startpos.endpos = startpos.startpos
        p[0] = PyClauseArgs(startpos,startpos)
        startpos = None
        return

    def p_insert_statement_args_1(self,p):
        ''' inner_statement_args : TEXT
                  | inner_statement_args TEXT
        '''
        if len(p) == 2:
            p[0] = PyClauseArgs(p.slice[1],p.slice[1])
            p[0].append_args(p.slice[1].value)
        elif len(p) == 3:
            p[0] = p[1]
            p[0].append_args(p.slice[2].value)
            p[0].set_endpos(p.slice[2])
            p[1] = None
        return


    def p_error(self,p):
        raise Exception('can not handle %s'%(repr(p)))


    def build(self,**kwargs):
        return yacc.yacc(module=self,start='statements',**kwargs)


    def format_clause(self,tabs):
        if self.statements is None:
            return ''
        return self.statements.format_clause(tabs)


def make_pyclause(s,tabs):
    lexinput = PyClauseLex()
    lexer = lexinput.build()
    lexer.input(s)
    yacchandle = PyClauseYacc()
    parser = yacchandle.build(tabmodule='pyclause')
    parser.parse(s)
    rets = yacchandle.format_clause(tabs)
    return rets