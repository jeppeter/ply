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

class PythonCodeLex(object):
    tokens = ['SEMI','LBRACE','RBRACE','COMMENT','TEXT']
    t_ignore = ''
    t_comment_ignore = ''
    t_newlinebegin_ignore = ''
    states = (
        ('comment','exclusive'),
        ('newlinebegin','exclusive'),
    )

    def __init__(self,deftabs=4):
        self.lineno = 1
        self.column = 1
        self.linepos = 0
        self.braces = 0
        self.doublequoted = 0
        self.commented = 0
        self.tabspace = deftabs
        self.lastspace = None
        return

    @lex.TOKEN(r'\#')
    def t_COMMENT(self,p):
        self.commented = 1
        p.lexer.push_state('comment')
        return None

    def t_comment_error(self,p):
        raise Exception('comment error')
        return

    def t_newlinebegin_error(self,p):
        raise Exception('comment error')
        return

    @lex.TOKEN('.')
    def t_comment_TEXT(self,p):
        curpos = p.lexer.lexpos - len(p.value)
        maxpos = len(p.lexer.lexdata)
        neednewlinebegin = False
        while curpos < maxpos:
            curch = p.lexer.lexdata[curpos]
            if curch == '\n':
                curpos += 1
                p.lexer.linepos = curpos
                neednewlinebegin = True                
                break
            curpos += 1
        self.comment = 0
        p.lexer.pop_state()
        p.lexer.lexpos = curpos
        if neednewlinebegin :
            # we count the new line begin
            p.lexer.push_state('newlinebegin')
        return None

    def set_empty_line(self,p,curpos):
        p.lexer.lexpos = curpos
        p.value = ''
        p.type = 'TEXT'
        p.startline = p.lexer.lineno
        p.startpos = curpos - p.lexer.linepos
        p.endline = p.lexer.lineno
        p.endpos = curpos - p.lexer.linepos
        p.lastspace = self.lastspace
        return p

    @lex.TOKEN(r'.')
    def t_newlinebegin_TEXT(self,p):
        curpos = p.lexer.lexpos - len(p.value)
        maxpos = len(p.lexer.lexdata)
        curspace = 0
        startpos = curpos - p.lexer.linepos
        while curpos < maxpos:
            curch = p.lexer.lexdata[curpos]
            if curch == ' ':
                curspace += 1
            elif curch == '\t':
                curspace += self.tabspace
            elif curch == '\n':
                p.lexer.lastspace = curspace
                self.lastspace = curspace
                self.step_linepos(p.lexer,curpos)
                curpos += 1
                # we for the next one as it will give the onely
                return self.set_empty_line(p,curpos)
            elif curch == '\r':
                pass
            elif curch == '#':
                # it is comment state
                self.lastspace = curspace
                p.lexer.lastspace = curspace
                p.lexer.pop_state()
                p.lexer.push_state('comment')
                return self.set_empty_line(p,curpos)
            else:
                break
            curpos += 1
        p.lexer.lexpos = curpos
        self.lastspace = curspace
        p.lexer.lastspace = curspace
        p.lexer.pop_state()
        return None

    def pass_longquote(self,p,startpos,triqs):
        valbuf = triqs
        curpos = startpos + 3
        maxpos = len(p.lexer.lexdata)
        slashed = False
        beginline = p.lexer.lineno
        beginpos = startpos - p.lexer.linepos
        startdata = p.lexer.lexdata[startpos]
        if len(startdata) > 20:
            startdata = startdata[:20]
        while curpos < maxpos:
            curch = p.lexer.lexdata[curpos]
            #logging.info("[%s:%s]lexdata (%s)"%(p.lexer.lineno,(curpos - p.lexer.linepos),curch))
            if slashed:
                slashed = False
                valbuf += curch
            elif p.lexer.lexdata[curpos:].startswith(triqs):
                curpos += 3
                valbuf += triqs
                break
            elif curch == '\r':
                valbuf += '\\r'
            elif curch == '\n':
                valbuf += '\\n'
                self.step_linepos(p.lexer,curpos)
                #logging.info('[%s:%s][%s]'%(p.lexer.lineno,0,curpos))
            elif curch == '\t':
                valbuf += '\\t'
            elif curch == '\\':
                slashed = True
                valbuf += curch
            else:
                valbuf += curch
            curpos += 1
        if curpos == maxpos:
            errstr = '[%s:%s] %s not ended quote string'%(beginline,beginpos,startdata)
        return (curpos - startpos),valbuf

    def pass_quote_inner(self,p,startpos,qs):
        data = p.lexer.lexdata[startpos:]
        triqs = qs * 3
        if data.startswith(triqs):
            return self.pass_longquote(p,startpos,triqs)
        valbuf = qs
        maxpos = len(p.lexer.lexdata)
        curpos = startpos + 1
        slashed = False
        while curpos < maxpos:
            curch = p.lexer.lexdata[curpos]
            if slashed :
                if curch == '\r' or curch == '\n':
                    linepos = curpos - p.lexer.linepos
                    errstr = 'can not get newline in quoted at [%s-%s]'%(p.lexer.lineno,linepos)
                    raise Exception(errstr)
                slashed = False
            elif curch == '\\':
                slashed = True
            elif curch == '\r' or curch == '\n':
                linepos = curpos - p.lexer.linepos
                errstr = 'can not get newline in quoted at [%s-%s]'%(p.lexer.lineno,linepos)
                raise Exception(errstr)
            elif curch == qs:
                valbuf += qs
                curpos += 1
                break
            valbuf += curch
            curpos += 1
        if curpos == maxpos:
            linepos = startpos - p.lexer.linepos
            raise Exception('not ended quote string at [%s-%s]'%(p.lexer.lineno,linepos))
        return (curpos - startpos),valbuf

    def step_linepos(self,lexer,curpos):
        lexer.lineno += 1
        lexer.linepos = (curpos+1)
        return


    @lex.TOKEN(r'.')
    def t_TEXT(self,p):
        if self.lastspace is None:
            p.lexer.lineno = 1
            p.lexer.linepos = 0
            p.lexer.push_state('newlinebegin')
            # we set to the begin
            p.lexer.lexpos = 0
            return None
        curpos = p.lexer.lexpos - len(p.value)
        startline = p.lexer.lineno
        startpos = curpos - p.lexer.linepos
        #logging.info('[%s:%s]curpos [%s] linepos [%s]'%(startline,startpos,curpos,p.lexer.linepos))
        maxpos = len(p.lexer.lexdata)
        valbuf = ''
        slashed = False
        newlinebegin = False
        commented = False
        linestarted = False
        while curpos < maxpos:
            curch = p.lexer.lexdata[curpos]
            if slashed:
                if curch == '\r':
                    pass
                elif curch == '\n':
                    self.step_linepos(p.lexer,curpos)
                    slashed = False
                    linestarted = True
                else:
                    logging.error('after slash with other words at %d'%(p.lexer.lineno))
                    slashed = False
                    valbuf += '\\'
                    valbuf += curch
                curpos += 1
            elif linestarted:
                if curch == ' ' or curch == '\t' or curch == '\r':
                    curpos += 1
                elif curch == '\n':
                    newlinebegin = True
                    self.step_linepos(p.lexer,curpos)
                    curpos += 1
                    break
                elif curch == '#':
                    commented = True
                    curpos += 1
                    break
                elif curch == '\\':
                    linestarted = False
                    slashed = True
                    curpos += 1
                elif curch == '\'' or curch == '"':
                    linestarted = False
                    valbuf += ' '
                    passed ,curbuf = self.pass_quote_inner(p,curpos,curch)
                    curpos += passed
                    valbuf += curbuf
                    logging.info('[%s:%s]'%(p.lexer.lineno,(curpos-p.lexer.linepos)))
                else:
                    linestarted = False
                    valbuf += ' '
                    valbuf += curch
                    curpos += 1                
            elif curch == '\'' or curch == '"':
                passed,curbuf = self.pass_quote_inner(p,curpos,curch)
                curpos += passed
                valbuf += curbuf
                #logging.info('[%s:%s][%s]'%(p.lexer.lineno,(curpos-p.lexer.linepos),curpos))
            elif curch == '\\':
                slashed = True
                curpos += 1
            elif curch == '\n':
                newlinebegin = True
                self.step_linepos(p.lexer,curpos)
                curpos += 1
                break
            elif curch == '\r':
                curpos += 1
            elif curch == '#':
                commented = True
                break
            else:
                valbuf += curch
                curpos += 1
        p.lexer.lexpos = curpos
        p.value = valbuf
        p.type = 'TEXT'
        p.startline = startline
        p.startpos = startpos
        p.endline = p.lexer.lineno
        p.lastspace = self.lastspace
        if curpos < maxpos:
            p.endpos = (curpos - 1 - p.lexer.linepos)
        else:
            p.endpos = curpos - p.lexer.linepos
        p.lexer.lastspace = self.lastspace
        if commented :
            p.lexer.push_state('comment')
        if newlinebegin:
            p.lexer.push_state('newlinebegin')
        return p

    def t_error(self,p):
        self.column = p.lexpos = (p.lexer.lexpos - p.lexer.linepos )
        raise Exception('at [%s:%s] error [%s]'%(self.lineno,self.column,p.value))
        return

    def build(self,**kwargs):
        lexer = lex.lex(module=self,**kwargs)
        lexer.linepos = 0
        return lexer



class PythonCode(object):
    def __init__(self,startelm=None,endelm=None):
        self.code = None
        self.space = None
        self.startline = 1
        self.startpos = 1
        self.endline = 1
        self.endpos = 1
        if startelm is not None:
            self.startline = startelm.startline
            self.startpos = startelm.startpos
        if endelm is not None:
            self.endline = endelm.endline
            self.endpos = endelm.endpos
        return

    def set_code(self,s,space):
        self.code = s
        self.space = space
        return

class PythonCodes(object):
    def __init__(self,deftabs=4,startelm=None,endelm=None):
        self.codes = []
        self.spaces = []
        self.deftabs = deftabs
        self.startline = 1
        self.startpos = 1
        self.endline = 1
        self.endpos = 1
        if startelm is not None:
            self.startline = startelm.startline
            self.startpos = startelm.startpos
        if endelm is not None:
            self.endline = endelm.endline
            self.endpos = endelm.endpos
        return

    def append_code(self,code,endelm=None):
        if code.code is not None:
            self.codes.append(code.code)
            self.spaces.append(code.space)
        if endelm is not None:
            self.endline = endelm.endline
            self.endpos = endelm.endpos
        return

    def quoted_string(self,s):
        rets = ''
        for c in s:
            if c == '\\':
                rets += '\\\\'
            elif c == '"':
                rets += '\\"'
            else:
                rets += c
        return rets

    def format_code(self,usequoted=True):
        s = ''
        assert(len(self.codes) == len(self.spaces))
        idx = 0
        beginspace = 0
        lastspace = 0
        while idx < len(self.codes):
            if idx == 0:
                beginspace = self.spaces[idx]
                lastspace = self.spaces[idx]
            curspace = self.spaces[idx]
            origspace = curspace
            if curspace < beginspace:
                raise Exception('[%d]can not handle unindent space[%d] < [%d]'%(idx,curspace,beginspace))
            if curspace > lastspace:
                while curspace > lastspace:
                    s += '{'
                    curspace -= self.deftabs
            elif curspace < lastspace:
                while curspace < lastspace:
                    s += '}'
                    curspace += self.deftabs
            if usequoted:
                s += self.quoted_string(self.codes[idx])
            else:
                s += self.codes[idx]
            s += ';'
            lastspace = self.spaces[idx]
            idx += 1
            if idx == len(self.codes) and origspace > beginspace:
                logging.info('curspace[%d] beginspace[%d]'%(origspace,beginspace))
                while origspace > beginspace:
                    s += '}'
                    origspace -= self.deftabs
        return s


class PythonCodeYacc(object):
    tokens = PythonCodeLex.tokens
    def __init__(self,deftabs=4):
        self.statements = None
        self.deftabs = deftabs
        return

    def set_statements(self,p):
        self.statements = p
        return

    def p_statements(self,p):
        ''' statements : statements statement
        '''
        p[0] = p[1]
        p[0].append_code(p[2],p[2])
        p[1] = None
        p[2] = None
        self.set_statements(p[0])
        return

    def p_statement(self,p):
        ''' statement : TEXT
        '''
        p[0] = PythonCode(p.slice[1],p.slice[1])
        p[0].set_code(p.slice[1].value,p.slice[1].lastspace)
        return

    def p_statements_empty(self,p):
        ''' statements : 
        '''
        startpos = location.Location()
        startpos.startline = p.lexer.lineno
        startpos.startpos = (p.lexer.lexpos-p.lexer.linepos)
        startpos.endline = startpos.startline
        startpos.endpos = startpos.startpos
        p[0] = PythonCodes(self.deftabs,startpos,startpos)
        startpos = None
        self.set_statements(p[0])
        #logging.info('p0 [%s]'%(repr(p[0])))
        return


    def p_error(self,p):
        raise Exception('can not handle %s'%(repr(p)))

    def build(self,**kwargs):
        return yacc.yacc(module=self,start='statements',**kwargs)

    def format_code(self,usequoted=True):
        if self.statements is not None:
            return self.statements.format_code(usequoted)
        return ''


def make_flat_code(s,tabwidth=4,usequoted=True):
    lexinput = PythonCodeLex()
    lexer = lexinput.build()
    yacchandle = PythonCodeYacc(tabwidth)
    parser = yacchandle.build(tabmodule='pycode')
    parser.parse(s)
    rets = yacchandle.format_code(usequoted)
    return rets
