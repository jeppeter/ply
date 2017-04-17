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

import ply.yacc as yacc
import dlex

class DhcpConfYacc(object):
	tokens = dlex.DhcpConfLex.tokens
	def __init__(self,lexer=None):
		self.lexer = lexer
		return

	def p_statements(self,p):
		''' statements : empty
				| statements statement
		'''
		return

	def p_statement(self,p):
		''' statement : host_statement
		'''
		return

	def p_host_statement(self,p):
		''' host_statement : HOST TEXT LBRACE declarations RBRACE
		'''
		return

	def p_declarations(self,p):
		''' declarations : empty
				| declarations declaration
		'''
		return

	def p_declaration(self,p):
		''' declaration : hardware_declaration
				| fixed_address_declaration
		'''
		return

	def p_hardware_declaration(self,p):
		''' hardware_declaration : HARDWARE hardware_type SEMI
		'''
		return

	def p_hardware_type(self,p):
		''' hardware_type : ETHERNET macaddr
		'''
		return

	def p_macaddr(self,p):
		''' macaddr : TEXT COLON TEXT COLON TEXT COLON TEXT COLON TEXT COLON TEXT
		'''
		logging.info('%s'%(repr(p)))
		return

	def p_error(self,p):
		raise Exception('find error %s'%(repr(p)))

	def p_fixed_address(self,p):
		''' fixed_address_declaration : FIXED_ADDRESS TEXT SEMI
		'''
		logging.info('%s'%(repr(p)))
		return

	def p_empty(self,p):
		''' empty :		
		'''
		return

	def build(self,**kwargs):
		return yacc.yacc(module=self,start='statements',**kwargs)

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
	dhcplex = dlex.DhcpConfLex()
	lexer = dhcplex.build()
	dhcpyacc = DhcpConfYacc(lexer)
	parser = dhcpyacc.build()
	parser.parse(s)



if __name__ == '__main__':
	main()



