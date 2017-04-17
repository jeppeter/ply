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

_insert_path(os.path.dirname(os.path.realpath(__file__)),'..','..')

import ply.lex as lex


class DhcpConfLex(object):
	reserved = {
		'fixed-address' : 'FIXED_ADDRESS',
		'ethernet' : 'ETHERNET',
		'hardware' : 'HARDWARE'
	}
	tokens = [ 'HOST','TEXT','COLON','SEMI','LBRACE','RBRACE'] + list(reserved.values())
	t_ignore = ' \t'
	def __init__(self):
		self.lineno = 1
		self.column = 1
		self.linepos = 0
		self.braces = 0
		return

	@lex.TOKEN(r'\:')
	def t_COLON(self,p):
		p.lineno = self.lineno
		p.lexpos = (p.lexer.lexpos - self.linepos)
		return p

	@lex.TOKEN(r'\;')
	def t_SEMI(self,p):
		p.lineno = self.lineno
		p.lexpos = (p.lexer.lexpos - self.linepos)
		return p

	@lex.TOKEN('host')
	def t_HOST(self,p):
		p.lineno = self.lineno
		p.lexpos = (p.lexer.lexpos - self.linepos)
		return p


	@lex.TOKEN('fixed-address')
	def t_FIXED_ADDRESS(self,p):
		p.lineno = self.lineno
		p.lexpos = (p.lexer.lexpos - self.linepos - len(p.value))
		return p

	@lex.TOKEN('hardware')
	def t_HARDWARE(self,p):
		p.lineno = self.lineno
		p.lexpos = (p.lexer.lexpos - self.linepos - len(p.value))
		return p

	@lex.TOKEN(r'[a-zA-Z\-_0-9\.]+')
	def t_TEXT(self,p):
		p.lineno = self.lineno
		p.lexpos = (p.lexer.lexpos - self.linepos - len(p.value))
		p.type = self.__class__.reserved.get(p.value,'TEXT')
		return p

	@lex.TOKEN(r'\{')
	def t_LBRACE(self,p):
		self.braces += 1
		p.lineno = self.lineno
		p.lexpos = (p.lexer.lexpos - self.linepos - len(p.value))
		return p

	@lex.TOKEN(r'\}')
	def t_RBRACE(self,p):
		self.braces -= 1
		p.lineno = self.lineno
		p.lexpos = (p.lexer.lexpos - self.linepos - len(p.value))
		return p

	def t_newline(self,p):
		r'\n'
		self.linepos = p.lexer.lexpos
		self.lineno += 1
		return None

	def t_carriage(self,p):
		r'\r'
		return None

	def t_error(self,p):
		self.column = p.lexer.lexpos - self.linepos
		raise Exception('at [%s:%s] error [%s]'%(self.lineno,self.column,p.value))
		return

	def build(self,**kwargs):
		return lex.lex(module=self,**kwargs)


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
	dhcplex = DhcpConfLex()
	lexer = dhcplex.build()
	lexer.input(s)
	while True:
		tok = lexer.token()
		if tok is None:
			break
		sys.stdout.write('(%s,%r,%d,%d)\n' % (tok.type, tok.value, tok.lineno, tok.lexpos))
	return

if __name__ == '__main__':
	main()

