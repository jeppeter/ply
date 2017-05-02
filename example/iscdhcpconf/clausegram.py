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

from funcgram import FunctionLex

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

    def p_statement_0(self,p):
        ''' statement : TEXT SEMI
        '''
        p[0] = Clause(p.slice[1].value,p.slice[1],p.slice[2])
        return

    def p_statement_1(self,p):
    	''' statement : SEMI
    	'''
    	p[0] = Clause('',p.slice[1],p.slice[1])
    	return

    def p_error(self,p):
        raise Exception('can not handle %s'%(repr(p)))


    def build(self,**kwargs):
        return yacc.yacc(module=self,start='statements',**kwargs)


    def format_clause(self,tabs):
        if self.statements is None:
            return ''
        return self.statements.format_clause(tabs)


def make_clause(prefix,s,tabs):
    lexinput = FunctionLex()
    lexer = lexinput.build()
    yacchandle = ClauseYacc(lexer,prefix)
    parser = yacchandle.build(tabmodule='clauseparse')
    parser.parse(s)
    rets = yacchandle.format_clause(tabs)
    return rets
