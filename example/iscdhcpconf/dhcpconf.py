#! /usr/bin/env python

import sys
import logging
import re
import time

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

	def format_config(self,tabs=0):
		s = ''
		for c in self.children:
			s += c.format_config(tabs)
		return s

	def set_endpos(self,endline=None,endpos=None):
		if endline is not None and endpos is not None:
			self.endline = endline
			self.endpos = endpos
		return

class MacAddress(YaccDhcpObject):
	def __init__(self,macaddr='0',children=None,startline=None,startpos=None,endline=None,endpos=None):
		super(MacAddress,self).__init__('MacAddress',children,startline,startpos,endline,endpos)
		self.macaddr = macaddr
		return

	def value_format(self):
		return '%s'%(self.macaddr)

	def append_colon_part(self,value,endline=None,endpos=None):
		self.macaddr += ':%s'%(value)
		self.set_endpos(endline,endpos)
		return True

	def check_valid_macaddr(self):
		sarr = re.split(':',self.macaddr)
		if len(sarr) != 6:
			return False
		hval = re.compile('^[0-9a-f]{1,2}$',re.I)
		for c in sarr:
			if not hval.match(c):
				return False
		return True


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


	def format_config(self,tabs):
		s = ''
		if len(self.children) > 0:
			for c in self.children:
				s += c.format_config(tabs)
				s += '\n'
		return s


class HostName(YaccDhcpObject):
	def __init__(self,typename=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'HostName'
		super(HostName,self).__init__(typename,None,startline,startpos,endline,endpos)
		self.hostname = None
		return

	def value_format(self):
		s = ''
		if self.hostname is not None:
			s = self.hostname
		return s

	def format_config(self,tabs=0):
		return self.value_format()

	def start_hostname(self,value):
		self.hostname= value
		return True

	def append_colone_text(self,value,endline=None,endpos=None):
		if self.hostname is None:
			return False
		self.hostname += ':%s'%(value)
		self.set_endpos(endline,endpos)
		return True

	def append_dot_text(self,value,endline=None,endpos=None):
		if self.hostname is None:
			return False
		self.hostname += '.%s'%(value)
		self.set_endpos(endline,endpos)
		return True



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


class SharedNetwork(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'SharedNetwork'
		super(SharedNetwork,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.sharedhost = ''
		return

	def value_format(self):
		return '%s'%(self.sharedhost)

	def set_shared_host(self,value):
		self.sharedhost = value
		return

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'shared-network %s {\n'%(self.sharedhost)
		for c in self.children:
			s += c.format_config((tabs + 1))
		s += ' ' * tabs * 4
		s += '}\n'
		return s

class SharedNetworkDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'SharedDeclarations'
		super(SharedNetworkDeclarations,self).__init__(typename,children,startline,startpos,endline,endpos)
		return


class SubnetStatement(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'SubnetStatement'
		super(SubnetStatement,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.ipaddr = None
		self.ipmask = None
		return

	def __format_ipaddr(self):
		s = '127.0.0.1'
		if self.ipaddr is not None:
			s = self.ipaddr
		return s

	def __format_ipmask(self):
		s = '255.255.255.0'
		if self.ipmask is not None:
			s = self.ipmask
		return s


	def value_format(self):
		return '%s netmask %s'%(self.__format_ipaddr(),self.__format_ipmask())

	def set_ipaddr(self,value):
		self.ipaddr = value
		return True

	def set_mask(self,value):
		self.ipmask = value
		return True


	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'subnet %s netmask %s {\n'%(self.__format_ipaddr(),self.__format_ipmask())
		for c in self.children:
			s += c.format_config((tabs + 1))
		s += ' ' * tabs * 4
		s += '}\n'
		return s

class SubNetworkDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'SubDeclarations'
		super(SubNetworkDeclarations,self).__init__(typename,children,startline,startpos,endline,endpos)
		return

	def format_config(self,tabs=0):
		s = ''
		logging.info('children %s'%(repr(self.children)))
		for c in self.children:
			s += c.format_config(tabs)
		return s


class InterfaceDeclaration(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'InterfaceDeclaration'
		super(InterfaceDeclaration,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.interface = ''
		return

	def value_format(self):
		return '%s'%(self.interface)

	def set_interface(self,value):
		self.interface = value
		return

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'interface %s ;\n'%(self.interface)
		return s


class IpAddress(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'IpAddress'
		super(IpAddress,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.ipv4addr = None
		self.ipv6addr = None
		return

	def __format_ipv4(self):
		s = ''
		if self.ipv4addr is not None:
			s += self.ipv4addr
		return s

	def set_ipv4_address(self,value):
		self.ipv4addr = value
		return True

	def start_ipv6_address(self,value,startline=None,startpos=None,endline=None,endpos=None):
		self.ipv6addr = value
		if startline is not None and startpos is not None \
			and endline is not None and endpos is not None:
			self.startline = startline
			self.startpos = startpos
			self.endline = endline
			self.endpos = endpos
		return True

	def append_ipv6_colon(self,endline=None,endpos=None):
		if self.ipv6addr is None:
			return False
		self.ipv6addr += ':'
		self.set_endpos(endline,endpos)
		return True

	def append_ipv6(self,value,endline=None,endpos=None):
		if self.ipv6addr is None:
			return False
		self.ipv6addr += ':'
		self.ipv6addr += value
		self.set_endpos(endline,endpos)
		return True

	def __format_ipv6(self):
		s = ''
		if self.ipv6addr is not None:
			s += self.ipv6addr
		return s

	def value_format(self,tabs=0):
		s = self.__format_ipv4()
		if len(s) > 0:
			return s
		return self.__format_ipv6()


	def format_config(self,tabs=0):		
		return self.value_format()

	def check_valid_address(self):		
		return True

	def check_valid_mask(self):
		return True


class DnsName(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'DnsName'
		super(IpAddress,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.dnsname = None
		return



	def value_format(self,tabs=0):
		s = ''
		if self.dnsname is not None:
			s += self.dnsname
		return s


	def format_config(self,tabs=0):		
		return self.value_format()

	def start_dnsname(self,value):
		self.dnsname = value
		return

	def append_dot_name(self,value,endline=None,endpos=None):
		if self.dnsname is None:
			return False
		self.dnsname += '.%s'%(value)
		self.set_endpos(endline,endpos)
		return

class InterfaceName(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'InterfaceName'
		super(InterfaceName,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.interfacename = None
		return

	def value_format(self,tabs=0):
		s = ''
		if self.interfacename is not None:
			s += self.interfacename
		return s


	def format_config(self,tabs=0):		
		return self.value_format()

	def start_interfacename(self,value):
		self.interfacename = value
		return

class OptionStatement(YaccDhcpObject):
	def __init__(self,typename=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'OptionStatement'
		super(OptionStatement,self).__init__(typename,None,startline,startpos,endline,endpos)
		self.routername  = None
		return

	def value_format(self,tabs=0):
		s = ''
		if self.routername is not None:
			s += self.routername
		return s


	def format_config(self,tabs=0):		
		s = ''
		if self.routername is not None:
			s += ' ' * tabs * 4
			s += 'option routers %s;\n'%(self.routername)
		return s

	def set_routername(self,value):
		self.routername = value
		return True

class SubnetDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = 'SubnetDeclarations'
		super(SubnetDeclarations,self).__init__(typename,children,startline,startpos,endline,endpos)
		return

	def value_format(self,tabs=0):
		return ''


	def format_config(self,tabs=0):		
		s = ''
		for c in self.children:
			s += c.format_config(tabs)
		return s

class Failover(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.failover = None
		return

	def set_no_failover(self):
		self.failover=  None
		return

	def set_failover(self,value):
		self.failover = value
		return

	def value_format(self):
		s = ''
		if self.failover is None:
			s = 'no failover peer'
		else:
			s = 'failover peer %s'%(self.failover)
		return s

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		if self.failover is None:
			s += 'no failover peer;\n'
		else:
			s += 'failover peer %s;\n'%(self.failover)
		return s

class IpRange(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.dynamicbootp = False
		self.rangestart = '0.0.0.0'
		self.rangeend = '0.0.0.0'
		return

	def set_dynamic(self,val=True):
		self.dynamicbootp = val
		return

	def value_format(self):
		s = ''
		if self.dynamicbootp:
			s += 'dynamic-bootp'
		else:
			s += '%s %s'%(self,rangestart,self.rangeend)
		return s

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		if self.dynamicbootp :
			s += 'range dynamic-bootp;\n'
		else:
			s += 'range %s %s;\n'%(self.rangestart,self.rangeend)
		return s

	def set_range_ips(self,startip,endip):
		self.rangestart = startip
		self.rangeend = endip
		return True


class PoolDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startline,startpos,endline,endpos)
		return

class PoolStatement(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startline,startpos,endline,endpos)
		return

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'pool {\n'
		for c in self.children:
			s += c.format_config((tabs+1))
		s += ' ' * tabs * 4
		s += '}\n'
		return s

class TimeFormat(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startline=None,startpos=None,endline=None,endpos=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startline,startpos,endline,endpos)
		self.time_year = None
		self.time_month = None
		self.time_day = None
		return

	def value_format(self):
		s = '%s/%s/%s'
