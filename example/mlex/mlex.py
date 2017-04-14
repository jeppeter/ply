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

lex_dict = {
	'ENCODE_INT' : r'encode-int',
	'LPAREN' : r'\(',
	'RPAREN' : r'\)',
	'LBRACE' : r'\{',
	'RBRACE' : r'\}',
	'OPTION' : 'option'
}

def format_eval_str(d):
	s = ''
	s += 'tokens = ['
	idx = 0
	for k in d:
		if idx > 0 :
			s += ','
		s += '\'%s\''%(k)
		idx += 1
	s += ']\n'
	for k in d:
		s += 't_%s = r\'%s\'\n'%(k,d[k])
	print ('s [%s]'%(s))
	return s

exec(format_eval_str(lex_dict))

def t_newline(p):
	r'\n+'
	p.lineno += p.value.count('\n')
	return

def t_error(p):
	raise Exception('error occur %s'%(repr(p.value)))

t_ignore = ' \t'

def main():
	lexer = lex.lex()
	for l in sys.stdin:
		lexer.input(l)
		while True:
			tok = lexer.token()
			if tok is None:
				break
			sys.stdout.write('(%s,%r,%d,%d)\n' % (tok.type, tok.value, tok.lineno, tok.lexpos))

if __name__ == '__main__':
	main()

