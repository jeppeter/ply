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
		startline = getattr(startelm,'startline',None)
		startpos = getattr(startelm,'startpos',None)
		endline = getattr(endelm,'endline',None)
		endpos = getattr(endelm,'endpos',None)
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
