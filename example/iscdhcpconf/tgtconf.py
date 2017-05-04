#! /usr/bin/env python

import sys
import logging
import re
import time


class YaccDhcpObject(object):
	def __init__(self,typename='',children=None,startelm=None,endelm=None):
		self.children = []
		self.parent = None
		self.typename = typename
		self.startline = 1
		self.startpos = 1
		self.endline = 1
		self.endpos = 1
		self.filename = '<stdin>'
		startline = getattr(startelm,'startline',None)
		startpos = getattr(startelm,'startpos',None)
		endline = getattr(endelm,'endline',None)
		endpos = getattr(endelm,'endpos',None)
		sfilename = getattr(startelm,'filename',None)
		efilename = getattr(endelm,'filename',None)
		if sfilename is not None :
			self.filename = sfilename
		if efilename is not None and self.filename == '<stdin>':
			self.filename = efilename		
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

	def location(self):
		return '%s:%s-%s:%s'%(self.startline,self.startpos,self.endline,self.endpos)

	def append_child_and_set_pos(self,*childs):
		for c in childs:
			if isinstance(c,list) or isinstance(c,tuple):
				for k in c:
					if k is not None and isinstance(c,object) \
					      and issubclass(k.__class__,YaccDhcpObject):
					      self.append_child(k)
					else:
						logging.error('%s not valid YaccDhcpObject'%(repr(k)))
			elif isinstance(c,object) and issubclass(c.__class__,YaccDhcpObject):
				self.append_child(c)
			else:
				logging.error('%s not valid YaccDhcpObject'%(repr(c)))
		self.set_pos_by_children()
		return self

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

	def format_children_config(self,tabs=0,splitline=True):
		s = ''
		idx = 0
		for c in self.children:
			s += c.format_config(tabs)
			idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		s += self.format_children_config(tabs)
		return s

	def set_startpos(self,startelm=None):
		startline = None
		startpos = None
		if startelm is not None:
			startline = getattr(startelm,'startline',None)
			startpos = getattr(startelm,'startpos',None)
		if startline is not None and startpos is not None:
			self.startline = startline
			self.startpos = startpos
		return


	def set_endpos(self,endelm=None):
		endline = None
		endpos = None
		if endelm is not None:
			endline = getattr(endelm,'endline',None)
			endpos = getattr(endelm,'endpos',None)
		if endline is not None and endpos is not None:
			self.endline = endline
			self.endpos = endpos
		return

	def if_need_quoted(self,s):
		if ' ' in s or '/' in s or \
			'\t' in s or '\\' in s: 
			return True
		return False

	def quoted_string(self,s):
		rets = '"%s"'%(s)
		return rets

	def safe_quote_string(self,s):
		if self.if_need_quoted(s):
			return self.quoted_string(s)
		return s

	def get_child(self,clsname,recursive=False,root=None):
		outsarr = []
		if root is None:
			root = self
		for c in root.children:
			if c.__class__.__name__ == clsname:
				outsarr.append(c)
			if recursive:
				outsarr.extend(self.get_child(clsname,recursive,c))
		return outsarr

	def is_need_quoted(self,s):
		for c in s:
			if c >= 'a' and c <= 'z':
				continue
			if c >= 'A' and c <= 'Z':
				continue
			if c >= '0' and c <= '9':
				continue
			if c == '_' or c == '-' :
				continue
			return True
		return False

	def quote_safe(self,s):
		rets = s
		if self.is_need_quoted(s):
			rets = ''
			rets += '"'
			for c in s:
				if c == '"':
					rets += '\\"'
				elif c == '\\':
					rets += '\\\\'
				else:
					rets += c
			rets += '"'
		return rets



class Statements(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(Statements,self).__init__(typename,children,startelm,endelm)
		return

class IncludeStatement(YaccDhcpObject):
	def __init__(self,includefile,startelm=None,endelm=None):
		typename = self.__class__.__name__
		super(IncludeStatement,self).__init__(typename,None,startelm,endelm)
		self.includefile = includefile
		return

	def value_format(self):
		return self.quote_safe(self.includefile)

	def format_config(self,tabs=0):
		s = ' ' * tabs * 4
		s += 'include %s\n'%(self.value_format())
		return s


class Path(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(Path,self).__init__(typename,children,startelm,endelm)
		self.path = None
		return

	def start_path(self,p):
		self.path = p
		return

	def append_path(self,*args):
		if self.path is None:
			raise Exception('path is not set')
		for c in args:
			self.path += c
		return

	def get_path(self):
		if self.path is None:
			raise Exception('path is not set')
		return self.path

	def value_format(self):
		s = ''
		if self.path is not None:
			s = self.quote_safe(self.path)
		return s

class IQNName(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(IQNName,self).__init__(typename,children,startelm,endelm)
		self.name = None
		return

	def start_name(self,name):
		self.name = name
		return

	def append_name(self,*args):
		if self.name is None:
			raise Exception('not set name')
		for c in args:
			self.name += c
		return

	def value_format(self):
		s = ''
		if self.name is not None:
			s = self.quote_safe(self.name)
		return s


class TargetStatement(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(TargetStatement,self).__init__(typename,children,startelm,endelm)
		self.targetname = None
		return

	def value_format(self):
		s = ''
		if self.targetname is not None:
			s = self.targetname.value_format()
		return s

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += '<target %s>\n'%(self.value_format())
		s += self.format_children_config((tabs + 1))
		s += ' ' * tabs * 4
		s += '</target>\n'
		return s

	def set_name(self,n):
		if not isinstance(n,object) or \
			not issubclass(n.__class__,IQNName):
			raise Exception('not valid IQNName')
		self.targetname = n
		return

class TargetSuffix(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(TargetSuffix,self).__init__(typename,children,startelm,endelm)
		return

class TargetDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(TargetDeclarations,self).__init__(typename,children,startelm,endelm)
		return

class BackingStoreDeclaration(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(BackingStoreDeclaration,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			s = self.children[0].value_format()
		logging.info('s [%s] children %s'%(s,repr(self.children)))
		return s

	def format_config(self,tabs=0):
		s = ' ' * tabs * 4
		s += 'backing-store'
		if len(self.value_format()) > 0:
			s += ' %s'%(self.value_format())
		s += '\n'
		return s

class DirectStoreDeclaration(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(DirectStoreDeclaration,self).__init__(typename,children,startelm,endelm)
		self.targetname = None
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			s = self.children[0].value_format()
		return s

	def format_config(self,tabs=0):
		s = ' ' * tabs * 4
		s += 'direct-store'
		if len(self.value_format()) > 0:
			s += ' %s'%(self.value_format())
		s += '\n'
		return s

class LLDName(YaccDhcpObject):
	def __init__(self,value,startelm=None,endelm=None):
		typename = self.__class__.__name__
		super(LLDName,self).__init__(typename,None,startelm,endelm)
		self.lldname =value
		return

	def value_format(self):
		s = ''
		s += self.quote_safe(self.lldname)
		return s

	def format_config(self,tabs=0):
		return self.value_format()

class DriverDeclaration(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(DriverDeclaration,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			s += self.children[0].value_format()
		return s

	def format_config(self,tabs=0):
		s = ' ' * tabs * 4
		s += 'driver %s\n'%(self.value_format())
		return s

class Ipv4Addr(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(Ipv4Addr,self).__init__(typename,children,startelm,endelm)
		self.ipaddr = None
		return

	def start_addr(self,value):
		self.ipaddr = value
		return

	def add_dot_text(self,value):
		if self.ipaddr is None:
			raise Exception('not set ipaddr yet')
		self.ipaddr += '.' + value
		return

	def value_format(self):
		s = ''
		if self.ipaddr is not None:
			s = self.ipaddr
		return s

	def format_config(self,tabs=0):
		return self.value_format()

class Ipv6Addr(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(Ipv6Addr,self).__init__(typename,children,startelm,endelm)
		self.ipaddr = None
		return

	def start_addr(self,value):
		self.ipaddr = value
		return

	def add_colon_text(self,value):
		if self.ipaddr is None:
			raise Exception('not set ipaddr yet')
		self.ipaddr += ':' + value
		return

	def add_colon(self):
		if self.ipaddr is None:
			raise Exception('not set ipaddr yet')
		self.ipaddr += ':'

	def value_format(self):
		s = ''
		if self.ipaddr is not None:
			s = self.ipaddr
		return s

	def format_config(self,tabs=0):
		return self.value_format()

class InitiatorAddress(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(InitiatorAddress,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			s += self.children[0].value_format()
		return s

	def format_config(self,tabs=0):
		s = ' ' * tabs * 4
		s += 'initiator-address %s\n'%(self.value_format())
		return s


class HostName(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(HostName,self).__init__(typename,children,startelm,endelm)
		self.hostname = None
		return

	def start_value(self,value):
		self.hostname = value
		return

	def append_value(self,value):
		if self.hostname is None:
			raise Exception('not set hostname yet')
		self.hostname += value
		return

	def value_format(self):
		s = ''
		if self.hostname is not None:
			s = self.hostname
		return s

	def format_config(self,tabs=0):
		return self.value_format()

class InitiatorName(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(InitiatorName,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			s += self.children[0].value_format()
		return s

	def format_config(self,tabs=0):
		s = ' ' * tabs * 4
		s += 'initiator-name %s\n'%(self.value_format())
		return s


class User(YaccDhcpObject):
	def __init__(self,value,startelm=None,endelm=None):
		typename = self.__class__.__name__
		super(User,self).__init__(typename,None,startelm,endelm)
		self.user = value
		return

	def value_format(self):
		s = '""'
		if self.user is not None:
			s = self.quoted_string(self.user)
		return s

	def format_config(self,tabs=0):
		return self.value_format()

class Password(YaccDhcpObject):
	def __init__(self,value,startelm=None,endelm=None):
		typename = self.__class__.__name__
		super(Password,self).__init__(typename,None,startelm,endelm)
		self.password = value
		return

	def value_format(self):
		s = '""'
		if self.password is not None:
			s = self.quoted_string(self.password)
		return s

	def format_config(self,tabs=0):
		return self.value_format()


class IncomingUser(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(IncomingUser,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 1:
			s += self.children[0].value_format()
			s += ' '
			s += self.children[1].value_format()
		return s

	def format_config(self,tabs=0):
		s = ' ' * tabs * 4
		s += 'incominguser %s\n'%(self.value_format())
		return s

class OutGoingUser(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(OutGoingUser,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 1:
			s += self.children[0].value_format()
			s += ' '
			s += self.children[1].value_format()
		return s

	def format_config(self,tabs=0):
		s = ' ' * tabs * 4
		s += 'outgoinguser %s\n'%(self.value_format())
		return s
