#! /usr/bin/env python

import sys
import os
import importlib

def _insert_path(path,*args):
	_curdir = os.path.join(path,*args)
	if _curdir  in sys.path:
		sys.path.remove(_curdir)
	sys.path.insert(0,_curdir)
	return

_insert_path(os.path.dirname(os.path.realpath(__file__)),'..','..')

import ply.lex as lex

lex_func_dict = {
	'ALL' : True
}

lex_dict = {
	'LPAREN' : r'\(',
	'RPAREN' : r'\)',
	'LBRACE' : r'\{',
	'RBRACE' : r'\}'
}


def format_tokens_str(*args):
	s = ''
	s += 'tokens = ['
	idx = 0
	for d in args:
		if isinstance(d,dict):
			for k in d:
				if idx > 0:
					s += ','
				s += '\'%s\''%(k)
				idx += 1
	s += ']\n'
	return s


def format_eval_str(d):
	s = ''
	for k in d:
		s += 't_%s = r\'%s\'\n'%(k,d[k])
	print ('s [%s]'%(s))
	return s


exec(format_tokens_str(lex_dict,lex_func_dict))
exec(format_eval_str(lex_dict))

def t_newline(p):
	r'\n+'
	p.lineno += p.value.count('\n')
	return

def t_error(p):
	raise Exception('error occur %s'%(repr(p.value)))

def t_ALL(p):
	r'[a-zA-Z0-9_\-]+'
	print('p %s type %s'%(repr(p.value),repr(p)))
	return


t_ignore = ' \t'

def main():
	lexer = lex.lex()
	while True:
		try:
			if sys.version[0] == '2':
				l = raw_input('input>')
			else:
				l = input('input>')
			if l is None:
				break
			print('l [%s]'%(repr(l)))
			lexer.input(l)
			while True:
				tok = lexer.token()
				if tok is None:
					break
				sys.stdout.write('(%s,%r,%d,%d)\n' % (tok.type, tok.value, tok.lineno, tok.lexpos))
		except EOFError:
			break

if __name__ == '__main__':
	main()

