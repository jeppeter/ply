#! /usr/bin/env python

import sys
import logging

class YaccDhcpObject(object):
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
					if issubclass(c.__class__,YaccDhcpObject):
						c.parent = self
						self.children.append(c)
					else:
						logging.error('%s child not YaccDhcpObject'%(repr(c)))
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
			if isinstance(c,object) or issubclass(c.__class__,YaccDhcpObject):
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
			if issubclass(self.parent.__class__,YaccDhcpObject):
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

class MacAddress(YaccDhcpObject):
	def __init__(self,macaddr='0:0:0:0:0:0',children=None,startline=None,startpos=None,endline=None,endpos=None):
		super(MacAddress,self).__init__('MacAddress',children,startline,startpos,endline,endpos)
		self.macaddr = macaddr
		return

	def value_format(self):
		return '%s'%(self.macaddr)

class HardwareType(YaccDhcpObject):
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




class HardwareDeclaration(YaccDhcpObject):
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

class FixedAddressDeclaration(YaccDhcpObject):
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

class Declaration(YaccDhcpObject):
	def __init__(self,children=None,startline=None,startpos=None,endline=None,endpos=None):
		super(Declaration,self).__init__('Declaration',children,startline,startpos,endline,endpos)
		return

	def format_config(self,tabs=0):
		s = ''
		if len(self.children) > 0:
			s += self.children[0].format_config(tabs)
		return s

class Declarations(YaccDhcpObject):
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
			if isinstance(child,object) and issubclass(child.__class__,YaccDhcpObject):
				child.parent = self
				self.children.append(child)
			else:
				logging.error('%s not YaccDhcpObject'%(repr(child)))
		return

	def format_config(self,tabs):
		s = ''
		if len(self.children) > 0:
			for c in self.children:
				s += c.format_config(tabs)
				s += '\n'
		return s


class HostName(YaccDhcpObject):
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
