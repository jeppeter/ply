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

class YaccBaseObject(object):
	def __init__(self,typename='',children=None,startline=None,startpos=None,endline=None,endpos=None):
		self.children = []
		self.parent = None
		self.typename = typename
		self.startline = 1
		self.startpos = 1
		self.endline = 1
		self.endpos = 1
		if startline is not None:
			self.startline = startline
		if startpos is not None:
			self.startpos = startpos
		if endline is not None:
			self.endline = endline
		if endpos is not None:
			self.endpos = endpos
		if children is not None:
			if isinstance(children,list) or isinstance(children,tuple):
				for c in children:
					if issubclass(c.__class__,YaccBaseObject):
						c.parent = self
						self.children.append(c)
					else:
						logging.error('%s child not YaccBaseObject'%(repr(c)))
			else:
				logging.error('not tuple or list for (%s)'%(repr(children)))
		return

	def __is_less(self,value,cmpvalue):
		if value is not None and cmpvalue is not None and \
			cmpvalue < value:
			return cmpvalue
		return value

	def __is_great(self,value,cmpvalue):
		if value is not None and cmpvalue is not None and \
			cmpvalue > value:
			return cmpvalue
		return value


	def set_pos_by_children(self):
		startline = None
		startpos = None
		endline = None
		endpos = None
		for c in self.children:
			if isinstance(c,object) or issubclass(c.__class__,YaccBaseObject):
				if startline is None:
					startline = c.startline
				if startpos is None:
					startpos = c.startpos
				if endline is None:
					endline = c.endline
				if endpos is None:
					endpos = c.endpos

				startline = self.__is_less(startline,c.startline)
				startpos = self.__is_less(startpos,c.startpos)
				endline = self.__is_great(endline,c.endline)
				endpos = self.__is_great(endpos,c.endpos)

		if startline is not None and startpos is not None \
			and endline is not None and endpos is not None:
			self.startline = startline
			self.startpos = startpos
			self.endline = endline
			self.endpos = endpos
		return


	def value_format(self):
		return ''

	def pointer_basic(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += '%s<%s>:[%s:%s-%s:%s]'%(self.__class__.__name__,id(self),self.startline,self.startpos,self.endline,self.endpos)
		return s

	def format_basic(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += '[%s:%s-%s:%s]%s [%s] (%s)\n'%(self.startline,self.startpos,self.endline,self.endpos,self.typename,id(self),self.value_format())
		if self.parent is not None:
			s += ' ' * tabs * 4
			s += 'parent : '
			if issubclass(self.parent.__class__,YaccBaseObject):
				s += '%s'%(self.parent.pointer_basic(0))
			else:
				s += '%s'%(repr(self.parent))
		else:
			s += 'parent None;'
		s += '\n'
		s += ' ' * tabs * 4
		s += 'children:\n'
		idx = 0
		s += ' ' * tabs * 4
		if len(self.children) > 0:
			s += '{\n'
		else:
			s += '{'
		for c in self.children:
			s += c.format_value(tabs+1)			
			idx += 1
			if idx < len(self.children):
				s += ','
			s += '\n'
		if len(self.children) > 0:
			s += ' ' * tabs * 4
		s += '}'
		return s

	def __str__(self):
		return self.format_basic()

	def __repr__(self):
		s = '%s(%s)'%(self.__class__.__name__,self.format_basic())
		return s

	def format_value(self,tabs=0):
		return self.format_basic(tabs)

	def format_config(self,tabs=0):
		s = ''
		for c in self.children:
			s += c.format_config(tabs)
		return s


class MacAddress(YaccBaseObject):
	def __init__(self,macaddr='0:0:0:0:0:0',children=None,startline=None,startpos=None,endline=None,endpos=None):
		super(MacAddress,self).__init__('MacAddress',children,startline,startpos,endline,endpos)
		self.macaddr = macaddr
		return

	def value_format(self):
		return '%s'%(self.macaddr)

class HardwareType(YaccBaseObject):
	def __init__(self,hardwaretype='',children=None,startline=None,startpos=None,endline=None,endpos=None):
		super(HardwareType,self).__init__('HardwareType',children,startline,startpos,endline,endpos)
		self.hardwaretype = hardwaretype
		return

	def value_format(self):
		return '%s'%(self.hardwaretype)

	def format_config(self,tabs=0):
		s = ''
		s += '%s'%(self.hardwaretype)
		return s



class HardwareDeclaration(YaccBaseObject):
	def __init__(self,children=None,startline=None,startpos=None,endline=None,endpos=None):
		super(HardwareDeclaration,self).__init__('HardwareDeclaration',children,startline,startpos,endline,endpos)
		return

	def format_config(self,tabs=0):
		s = ''
		if len(self.children) > 1:
			s += ' ' * tabs * 4
			s += 'hardware '
			s += self.children[0].format_config(tabs + 1)
			s += ' '
			s += self.children[1].value_format()
			s += ';'
		return s

class FixedAddressDeclaration(YaccBaseObject):
	def __init__(self,fixedaddress='',children=None,startline=None,startpos=None,endline=None,endpos=None):
		super(FixedAddressDeclaration,self).__init__('FixedAddressDeclaration',children,startline,startpos,endline,endpos)
		self.fixedaddress = fixedaddress
		return

	def value_format(self):
		return self.fixedaddress

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'fixed-address %s;'%(self.fixedaddress)
		return s

class Declaration(YaccBaseObject):
	def __init__(self,children=None,startline=None,startpos=None,endline=None,endpos=None):
		super(Declaration,self).__init__('Declaration',children,startline,startpos,endline,endpos)
		return

	def format_config(self,tabs=0):
		s = ''
		if len(self.children) > 0:
			s += self.children[0].format_config(tabs)
		return s

class Declarations(YaccBaseObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'Declarations'
		super(Declarations,self).__init__(typename,children,startline,startpos,endline,endpos)
		return

	def extend_children(self,children=[]):
		for c in children:
			self.append_child(c)
		return

	def append_child(self,child):
		if child is not None:
			if isinstance(child,object) and issubclass(child.__class__,YaccBaseObject):
				child.parent = self
				self.children.append(child)
			else:
				logging.error('%s not YaccBaseObject'%(repr(child)))
		return

	def format_config(self,tabs):
		s = ''
		if len(self.children) > 0:
			for c in self.children:
				s += c.format_config(tabs)
				s += '\n'
		return s

class HostName(YaccBaseObject):
	def __init__(self,name=None,typename=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'HostName'
		super(HostName,self).__init__(typename,None,startline,startpos,endline,endpos)
		self.name = ''
		if name is not None:
			self.name = name
		return


	def value_format(self):
		return '%s'%(self.name)

class HostStatement(Declarations):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'HostStatement'
		super(HostStatement,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.hostname = None
		return

	def set_hostname(self,hostnamecls=None):
		if issubclass(hostnamecls.__class__,HostName):
			self.hostname = hostnamecls
		return

	def value_format(self):
		if self.hostname is None:
			return ''
		return '%s'%(self.hostname.value_format())


	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		if self.hostname is not None:
			s += 'host %s {\n'%(self.hostname.value_format())
		else:
			s += 'host {\n'
		for c in self.children:
			s += c.format_config(tabs+1)
		s += ' ' * tabs * 4
		s += '}\n'
		return s



class Statement(HostStatement):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'Statement'
		super(Statement,self).__init__(typename,children,startline,startpos,endline,endpos)
		return

	def format_config(self,tabs=0):
		s = ''
		for c in self.children:
			s += c.format_config(tabs)
		return s

class Statements(Statement):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'Statements'
		super(Statements,self).__init__(typename,children,startline,startpos,endline,endpos)
		return




class DhcpConfYacc(object):
	tokens = dlex.DhcpConfLex.tokens
	def __init__(self,lexer=None):
		self.lexer = lexer
		self.statements = None
		return

	def format_config(self):
		s = ''
		if self.statements is not None:
			#logging.info('statements %s'%(repr(self.statements)))
			s += self.statements.format_config()
		return s

	def p_statements(self,p):
		''' statements : empty
				| statements statement
		'''
		if len(p) == 2:
			statements = Statements(None,None,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
		else:
			statements = Statements()
			statements.extend_children(p[1].children)
			statements.append_child(p[2])
			statements.set_pos_by_children()
			p[1] = None
		p[0] = statements
		if self.statements is not None:
			self.statements = None
		self.statements = statements
		#logging.info('%s'%(repr(p[0])))
		return

	def p_statement(self,p):
		''' statement : host_statement
		'''
		children = []
		children.append(p[1])
		p[0] = Statement(None,children,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
		return

	def p_host_statement(self,p):
		''' host_statement : HOST host_name LBRACE declarations RBRACE
		'''
		children = []
		# this is for declarations
		children.append(p[4])
		p[0] = HostStatement(None,children,p.slice[1].startline,p.slice[1].startpos,p.slice[5].endline,p.slice[5].endpos) 
		p[0].set_hostname(p[2])
		p[2] = None
		return

	def p_host_name(self,p):
		''' host_name : 
			  | TEXT
		'''
		hostname = HostName(p.slice[1].value,None,p.slice[1].startline,p.slice[1].startpos,p.slice[1].endline,p.slice[1].endpos)
		p[0] = hostname
		return

	def p_declarations(self,p):
		''' declarations : empty
				| declarations declaration
		'''
		if len(p) == 2:
			declarations = Declarations(None,None,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
			p[1] = None
		else:
			declarations = Declarations(None,None,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
			declarations.extend_children(p[1].children)
			declarations.append_child(p[2])
			declarations.set_pos_by_children()
			p[1] = None
		p[0] = declarations
		return

	def p_declaration(self,p):
		''' declaration : hardware_declaration
				| fixed_address_declaration
		'''
		children = []
		children.append(p[1])
		p[0] = Declaration(children)
		p[0].set_pos_by_children()
		#logging.info('%s'%(repr(p[0])))
		return

	def p_hardware_declaration(self,p):
		''' hardware_declaration : HARDWARE hardware_type SEMI
		'''
		p[0] = p[2]
		return

	def p_hardware_type(self,p):
		''' hardware_type : ETHERNET macaddr
		'''
		hardwaretype = HardwareType('ethernet',None,p.slice[1].startline,p.slice[1].startpos,p.slice[1].endline,p.slice[1].endpos)
		children = []
		children.append(hardwaretype)
		children.append(p[2])
		hardware = HardwareDeclaration(children)
		hardware.set_pos_by_children()
		p[0] = hardware
		return

	def p_macaddr(self,p):
		''' macaddr : TEXT COLON TEXT COLON TEXT COLON TEXT COLON TEXT COLON TEXT
		'''
		macaddr = ''
		for i in p.slice[1:]:
			macaddr += i.value
		macobj = MacAddress(macaddr,None,p.slice[1].startline,p.slice[1].startpos,p.slice[6].endline,p.slice[6].endpos)
		p[0] = macobj
		return

	def p_error(self,p):
		raise Exception('find error %s'%(repr(p)))

	def p_fixed_address(self,p):
		''' fixed_address_declaration : FIXED_ADDRESS TEXT SEMI
		'''
		p[0] = FixedAddressDeclaration(p.slice[2].value,None,p.slice[1].startline,p.slice[1].startpos,p.slice[2].endline,p.slice[2].endpos)
		return

	def p_empty(self,p):
		''' empty :		
		'''
		p[0] = YaccBaseObject('Empty',None,p.lexer.lineno,(p.lexer.lexpos-p.lexer.linepos),p.lexer.lineno,(p.lexer.lexpos-p.lexer.linepos))
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
	s = dhcpyacc.format_config()
	sys.stdout.write('%s'%(s))
	return

if __name__ == '__main__':
	main()



