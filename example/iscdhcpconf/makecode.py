#! /usr/bin/env python

import sys
import os
import importlib
import extargsparse
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
					curpos += 1
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
					return p
				elif curch == '\#':
					curpos += 1
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
	def __init__(self,s):
		self.code= s
		return

class FunctionCodes(object):
	def __init__(self,tabs=0):
		self.curtab = tabs
		self.codes = []
		self.codetabs = []
		self.precodes = []
		self.precodetabs = []
		return

	def append_code(self,s):
		self.codes.append(self.curtab)
		self.codetabs.append(s)
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
		while idx < len(self.codes):
			s += self.__format_code(self.codes[idx],self.codetabs[idx])
			idx += 1
		return s

class FunctionYacc(object):
    tokens = FunctionLex.tokens
    def __init__(self,lexer=None,tabs=0):
        self.lexer = lexer
        self.statements = None
        self.tabs = tabs
        return

    def set_statements(self,p):
    	if self.statements is not None:
    		self.statements.extend_codes(p)
    	else:
    		self.statements = p
    	return


    def p_statements_emtpy(self,p):
    	'''statements : 
    	'''
    	p[0] =FunctionCodes(self.tabs) 
    	self.set_statements(p[0])
    	return

    def p_statements_brace(self,p):
    	''' statements : LBRACE statements RBRACE
    	'''
    	p[0] = p[2]
    	p[0].brace_code()
    	p[2] = None
    	self.set_statements(p[0])
    	return

    def p_statements_one(self,p):
    	''' statements : statements statement
    	'''
    	p[1].append_code(p[2].code)
    	p[0] = p[1]
    	p[1] = None
    	p[2] = None
    	self.set_statements(p[0])
    	return

    def p_statement_emtpy(self,p):
    	''' statement : SEMI
    	'''
    	p[0] = FunctionCode('')
    	return

    def p_statement_text(self,p):
    	''' statement : TEXT SEMI
    	'''
    	p[0] = FunctionCode(p.slice[1].value)
    	return

    def p_error(self,p):
    	raise Exception('can not handle')

    def build(self,**kwargs):
        return yacc.yacc(module=self,start='statements',**kwargs)


    def format_code(self):
    	if self.statements is None:
    		return ''
    	return self.statements.format_code()


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


def main():
    command='''
    {
        "verbose|v" : "+",
        "input|i" : null
    }
    '''
    parser = extargsparse.ExtArgsParse()
    parser.load_command_line_string(command)
    args = parser.parse_command_line()
    set_logging(args)
    s = read_file(args.input)
    lexinput = FunctionLex()
    lexer = lexinput.build()
    yacchandle = FunctionYacc(lexer)
    parser = yacchandle.build()
    parser.parse(s)
    s = yacchandle.format_code()
    sys.stdout.write('%s'%(s))
    return

if __name__ == '__main__':
	main()
