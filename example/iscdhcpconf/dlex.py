#! /usr/bin/env python

import sys
import os
import importlib
import extargsparse
import logging
import re

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
		'host' : 'HOST',
		'fixed-address' : 'FIXED_ADDRESS',
		'ethernet' : 'ETHERNET',
		'hardware' : 'HARDWARE',
		'shared-network' : 'SHARED_NETWORK',
		'interface' : 'INTERFACE',
		'subnet' : 'SUBNET',
		'netmask' : 'NETMASK',
		'option' : 'OPTION',
		'routers' : 'ROUTERS',
		'pool' : 'POOL',
		'allow' : 'ALLOW',
		'members' : 'MEMBERS',
		'of' : 'OF',
		'range' : 'RANGE',
		'range6' : 'RANGE6',
		'deny' : 'DENY',
		'no' : 'NO',
		'failover' : 'FAILOVER',
		'peer' : 'PEER',
		'dynamic-bootp' : 'DYNAMIC_BOOTP',
		'unknown' : 'UNKNOWN',
		'known-clients' : 'KNOWN_CLIENTS',
		'unknown-clients' : 'UNKNOWN_CLIENTS',
		'known' : 'KNOWN',
		'authenticated' : 'AUTHENTICATED',
		'unauthenticated' : 'UNAUTHENTICATED',
		'all' : 'ALL',
		'dynamic' : 'DYNAMIC',
		'bootp' : 'BOOTP',
		'never' : 'NEVER',
		'epoch' : 'EPOCH',
		'after' : 'AFTER',
		'prefix6' : 'PREFIX6',
		'fixed-prefix6' : 'FIXED_PREFIX6',
		'authoritative' : 'AUTHORITATIVE',
		'not' : 'NOT',
		'text' : 'TOKEN_TEXT'
	}
	tokens = ['TEXT','COLON','SEMI','LBRACE','RBRACE','DOUBLEQUOTE','COMMENT','DOT','NUMBER','SLASH','PLUS'] + list(reserved.values())
	t_ignore = ' \t'
	t_doublequoted_ignore = ''	
	t_comment_ignore = ''
	states = (
		('doublequoted','exclusive'),
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

	@lex.TOKEN(r'\.')
	def t_DOT(self,p):
		p.startline = p.lexer.lineno
		p.startpos = p.lexer.lexpos - len(p.value) - p.lexer.linepos
		p.endline = p.lexer.lineno
		p.endpos = p.lexer.lexpos - p.lexer.linepos
		return p


	@lex.TOKEN(r'\"')
	def t_DOUBLEQUOTE(self,p):
		self.doublequote = 1
		p.lexer.push_state('doublequoted')
		return

	@lex.TOKEN(r'\#')
	def t_COMMENT(self,p):
		self.commented = 1
		p.lexer.push_state('comment')
		return None

	@lex.TOKEN(r'\/')
	def t_SLASH(self,p):
		p.startline = p.lexer.lineno
		p.startpos = (p.lexer.lexpos - p.lexer.linepos - len(p.value))
		p.endpos = p.startpos + len(p.value)
		p.endline = p.startline
		return p

	@lex.TOKEN(r'\+')
	def t_PLUS(self,p):
		p.startline = p.lexer.lineno
		p.startpos = (p.lexer.lexpos - p.lexer.linepos - len(p.value))
		p.endpos = p.startpos + len(p.value)
		p.endline = p.startline
		return p

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
			curpos += 1
		self.comment = 0
		p.lexer.pop_state()
		p.lexer.lexpos = curpos
		return None

	def t_doublequoted_error(self,p):
		raise Exception('quoted error')
		return

	@lex.TOKEN('.')
	def t_doublequoted_TEXT(self,p):
		s = ''
		slashed = False
		if p.value == '"':
			p.startline = p.lexer.lineno
			p.startpos = (p.lexer.lexpos - p.lexer.linepos - len(p.value))
			p.endpos = p.startpos + len(p.value)
			p.endline = p.startline
			p.value = s
			return p
		elif p.value != '\\':
			s += p.value
		else:
			slashed = True
		quoted = True
		startpos = (p.lexer.lexpos - p.lexer.linepos - len(p.value))
		startline = p.lexer.lineno
		curpos = p.lexer.lexpos
		while curpos < len(p.lexer.lexdata):
			curch = p.lexer.lexdata[curpos]
			if slashed :
				if curch == 'n' :
					s += '\n'
				elif curch == 't':
					s += '\t'
				elif curch == 'b':
					if len(s) > 1:
						s = s[:-2]
					else:
						raise Exception('can not accept one length')
				else:
					s += curch
				slashed = False
			elif curch == '"':
				quoted = False
				curpos += 1
				break
			elif curch == '\\':
				slashed = True
			elif curch == '\n':
				p.lexer.lineno += 1
				p.lexer.linepos = curpos
				s += curch
			else:
				s += curch
			curpos += 1
		if quoted or slashed:
			raise Exception('not closed string %s'%(p.lexer.lexdata[startpos:]))
		p.startline = startline
		p.startpos = startpos
		p.endline = p.lexer.lineno
		p.endpos = ( curpos - p.lexer.linepos)
		p.lexer.lexpos = curpos
		p.value = s
		p.lexer.pop_state()
		self.doublequote = 0
		return p


	@lex.TOKEN(r'\:')
	def t_COLON(self,p):
		p.startline = p.lexer.lineno
		p.startpos = (p.lexer.lexpos - p.lexer.linepos - len(p.value))
		p.endpos = p.startpos + len(p.value)
		p.endline = p.startline
		#logging.info('COLON lineno [%s] lexpos [%s]'%(p.lineno,p.lexpos))
		return p

	@lex.TOKEN(r'\;')
	def t_SEMI(self,p):
		p.startline = p.lexer.lineno
		p.startpos = (p.lexer.lexpos - p.lexer.linepos - len(p.value))
		p.endpos = p.startpos + len(p.value)
		p.endline = p.startline
		#logging.info('SEMI lineno [%s] lexpos [%s]'%(p.lineno,p.lexpos))
		return p




	@lex.TOKEN(r'[a-zA-Z_0-9_\-][a-zA-Z\-_0-9]*')
	def t_TEXT(self,p):
		p.startline = p.lexer.lineno
		p.startpos = (p.lexer.lexpos - p.lexer.linepos - len(p.value))
		p.endpos = p.startpos + len(p.value)
		p.endline = p.startline
		p.type = self.__class__.reserved.get(p.value,'TEXT')
		decre = re.compile('^[0-9]+$',re.I)
		hexre = re.compile('^[a-f0-9]+$',re.I)
		if p.type == 'TEXT':
			if decre.match(p.value):
				p.type = 'NUMBER'
			elif len(p.value) > 1:
				matchvalue = None
				if p.value.startswith('0x') or p.value.startswith('0X'):
					matchvalue = p.value[2:]
				if matchvalue is not None:
					if hexre.match(matchvalue):
						p.type = 'NUMBER'

		#logging.info('TEXT lineno [%s] lexpos [%s]'%(p.lineno,p.lexpos))
		return p

	@lex.TOKEN(r'\{')
	def t_LBRACE(self,p):
		self.braces += 1
		p.startline = p.lexer.lineno
		p.startpos = (p.lexer.lexpos - p.lexer.linepos - len(p.value))
		p.endpos = p.startpos + len(p.value)
		p.endline = p.startline
		#logging.info('LBRACE lineno [%s] lexpos [%s]'%(p.lineno,p.lexpos))
		return p

	@lex.TOKEN(r'\}')
	def t_RBRACE(self,p):
		self.braces -= 1
		p.startline = p.lexer.lineno
		p.startpos = (p.lexer.lexpos - p.lexer.linepos - len(p.value))
		p.endpos = p.startpos + len(p.value)
		p.endline = p.startline
		#logging.info('RBRACE lineno [%s] lexpos [%s]'%(p.lineno,p.lexpos))
		return p

	def t_newline(self,p):
		r'\n'
		p.lexer.linepos = p.lexer.lexpos
		p.lexer.lineno += 1
		return None

	def t_carriage(self,p):
		r'\r'
		return None

	def t_error(self,p):
		self.column = p.lexpos = (p.lexer.lexpos - p.lexer.linepos )
		raise Exception('at [%s:%s] error [%s]'%(self.lineno,self.column,p.value))
		return

	def build(self,**kwargs):
		lexer = lex.lex(module=self,**kwargs)
		lexer.linepos = 0
		return lexer


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
		sys.stdout.write('(%s,%r,%d,%d)\n' % (tok.type, tok.value, tok.startline, tok.startpos))
	return

if __name__ == '__main__':
	main()

