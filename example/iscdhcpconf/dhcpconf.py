#! /usr/bin/env python

import sys
import logging
import re
import time

class Location(object):
    def __init__(self,startline=None,startpos=None,endline=None,endpos=None):
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
        return

    def __format(self):
        s = '[%s:%s-%s:%s]'%(self.startline,self.startpos,self.endline,self.endpos)
        return s

    def __str__(self):
        return self.__format()

    def __repr__(self):
        return self.__format()

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
			if idx > 0 and splitline:
				s += ' '* tabs * 4
				s += '\n'
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


class MacAddress(YaccDhcpObject):
	def __init__(self,macaddr='0',children=None,startelm=None,endelm=None):
		super(MacAddress,self).__init__('MacAddress',children,startelm,endelm)
		self.macaddr = macaddr
		return

	def value_format(self):
		return '%s'%(self.macaddr)

	def append_colon_part(self,value,endelm=None):
		self.macaddr += ':%s'%(value)
		self.set_endpos(endelm)
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
	def __init__(self,hardwaretype='',children=None,startelm=None,endelm=None):
		super(HardwareType,self).__init__('HardwareType',children,startelm,endelm)
		self.hardwaretype = hardwaretype
		return

	def value_format(self):
		return '%s'%(self.hardwaretype)

	def format_config(self,tabs=0):
		s = ''
		s += '%s'%(self.hardwaretype)
		return s




class HardwareDeclaration(YaccDhcpObject):
	def __init__(self,children=None,startelm=None,endelm=None):
		super(HardwareDeclaration,self).__init__('HardwareDeclaration',children,startelm,endelm)
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
	def __init__(self,fixedaddress='',children=None,startelm=None,endelm=None):
		super(FixedAddressDeclaration,self).__init__('FixedAddressDeclaration',children,startelm,endelm)
		self.fixedaddress = fixedaddress
		return

	def value_format(self):
		return self.fixedaddress

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'fixed-address %s;\n'%(self.fixedaddress)
		return s

class Declaration(YaccDhcpObject):
	def __init__(self,children=None,startelm=None,endelm=None):
		super(Declaration,self).__init__('Declaration',children,startelm,endelm)
		return

	def format_config(self,tabs=0):
		s = ''
		if len(self.children) > 0:
			s += self.children[0].format_config(tabs)
		return s

class Declarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'Declarations'
		super(Declarations,self).__init__(typename,children,startelm,endelm)
		return


	def format_config(self,tabs):
		s = ''
		s += self.format_children_config(tabs)
		return s


class HostName(YaccDhcpObject):
	def __init__(self,typename=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'HostName'
		super(HostName,self).__init__(typename,None,startelm,endelm)
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

	def append_colone_text(self,value,endelm=None):
		if self.hostname is None:
			return False
		self.hostname += ':%s'%(value)
		self.set_endpos(endelm)
		return True

	def append_dot_text(self,value,endelm=None):
		if self.hostname is None:
			return False
		self.hostname += '.%s'%(value)
		self.set_endpos(endelm)
		return True



class HostStatement(Declarations):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'HostStatement'
		super(HostStatement,self).__init__(typename,children,startelm,endelm)
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
		s += self.format_children_config((tabs+1))
		s += ' ' * tabs * 4
		s += '}\n'
		return s

class Statement(HostStatement):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'Statement'
		super(Statement,self).__init__(typename,children,startelm,endelm)
		return

	def format_config(self,tabs=0):
		s = ''
		s += self.format_children_config(tabs)
		return s

class Statements(Statement):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'Statements'
		super(Statements,self).__init__(typename,children,startelm,endelm)
		return


class SharedNetwork(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'SharedNetwork'
		super(SharedNetwork,self).__init__(typename,children,startelm,endelm)
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
		s += self.format_children_config((tabs+1))
		s += ' ' * tabs * 4
		s += '}\n'
		return s

class SharedNetworkDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'SharedDeclarations'
		super(SharedNetworkDeclarations,self).__init__(typename,children,startelm,endelm)
		return


class SubnetStatement(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'SubnetStatement'
		super(SubnetStatement,self).__init__(typename,children,startelm,endelm)
		self.ipaddr = None
		self.ipmask = None
		return

	def __format_ipaddr(self):
		s = '127.0.0.1'
		if self.ipaddr is not None:
			s = self.ipaddr.value_format()
		return s

	def __format_ipmask(self):
		s = '255.255.255.0'
		if self.ipmask is not None:
			s = self.ipmask.value_format()
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
		s += self.format_children_config((tabs+1))
		s += ' ' * tabs * 4
		s += '}\n'
		return s

class SubNetworkDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'SubDeclarations'
		super(SubNetworkDeclarations,self).__init__(typename,children,startelm,endelm)
		return

	def format_config(self,tabs=0):
		s = ''
		s += self.format_children_config(tabs)
		return s




class IpAddress(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'IpAddress'
		super(IpAddress,self).__init__(typename,children,startelm,endelm)
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

	def start_ipv6_address(self,value,startelm=None,endelm=None):
		self.ipv6addr = value
		if startelm.startline is not None and startelm.startpos is not None \
			and endelm.endline is not None and endelm.endpos is not None:
			self.startline = startelm.startline
			self.startpos = startelm.startpos
			self.endline = endelm.endline
			self.endpos = endelm.endpos
		return True

	def append_ipv6_colon(self,endelm=None):
		if self.ipv6addr is None:
			return False
		self.ipv6addr += ':'
		self.set_endpos(endelm)
		return True

	def append_ipv6(self,value,endelm=None):
		if self.ipv6addr is None:
			return False
		self.ipv6addr += ':'
		self.ipv6addr += value
		self.set_endpos(endelm)
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
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'DnsName'
		super(DnsName,self).__init__(typename,children,startelm,endelm)
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

	def append_dot_name(self,value,endelm=None):
		if self.dnsname is None:
			return False
		self.dnsname += '.%s'%(value)
		self.set_endpos(endelm)
		return

class DomainList(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'DomainList'
		super(DomainList,self).__init__(typename,children,startelm,endelm)
		return


	def value_format(self):
		s = ''
		idx = 0
		for c in self.children:
			if idx > 0:
				s += ','
			s += c.value_format()
			idx += 1
		return s

	def format_config(self,tabs=0):
		return self.value_format()




class OptionStatement(YaccDhcpObject):
	def __init__(self,typename=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'OptionStatement'
		super(OptionStatement,self).__init__(typename,None,startelm,endelm)
		self.option_format  = None
		return

	def value_format(self,tabs=0):
		s = ''
		if self.option_format is not None:
			s += self.option_format
		return s


	def format_config(self,tabs=0):		
		s = ''
		s += ' ' * tabs * 4
		s += '%s;\n'%(self.value_format())
		return s

	def set_routername(self,value):
		self.option_format = 'option routers %s'%(value)
		return True

class SubnetDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'SubnetDeclarations'
		super(SubnetDeclarations,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self,tabs=0):
		return ''


	def format_config(self,tabs=0):		
		s = ''
		s += self.format_children_config(tabs)
		return s

class Failover(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
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
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		self.dynamicbootp = False
		self.rangestart = '0.0.0.0'
		self.rangeend = '0.0.0.0'
		self.mode = 'range'
		return

	def set_mode(self,mode):
		self.mode = mode
		return True

	def set_dynamic(self,val=True):
		self.dynamicbootp = val
		return

	def value_format(self):
		s = ''
		if self.dynamicbootp:
			s += '%s dynamic-bootp'%(self.mode)
		else:
			s += '%s %s %s'%(self.mode,self,rangestart,self.rangeend)
		return s

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		if self.dynamicbootp :
			s += '%s dynamic-bootp;\n'%(self.mode)
		else:
			s += '%s %s %s;\n'%(self.mode,self.rangestart,self.rangeend)
		return s

	def set_range_ips(self,startip,endip):
		self.rangestart = startip
		self.rangeend = endip
		return True


class PoolDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		return

class PoolStatement(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		return

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'pool {\n'
		s += self.format_children_config((tabs+1))
		s += ' ' * tabs * 4
		s += '}\n'
		return s

class DayFormat(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		curtime = time.gmtime()
		self.time_year = curtime.tm_year
		self.time_month = curtime.tm_mon
		self.time_day = curtime.tm_mday
		return

	def value_format(self):
		return '%s/%s/%s'%(self.time_year,self.time_month,self.time_day)

	def format_config(self,tabs=0):
		return self.value_format()

	def set_year(self,year):
		self.time_year = int(year)
		return True

	def set_month(self,month):
		self.time_month = int(month)
		return True

	def set_day(self,day):
		self.time_day = int(day)
		return True

class TimeFormat(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		curtime = time.gmtime()
		self.time_hour = curtime.tm_hour
		self.time_minute = curtime.tm_min
		self.time_second = curtime.tm_sec
		return

	def value_format(self):
		return '%s:%s:%s'%(self.time_hour,self.time_minute,self.time_second)

	def format_config(self,tabs=0):
		return self.value_format()

	def set_hour(self,hour):
		self.time_hour = int(hour)
		return True

	def set_minute(self,minute):
		self.time_minute = int(minute)
		return True

	def set_second(self,second):
		self.time_second = int(second)
		return True

class DateFormat(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		self.special_format = None
		curtime = time.gmtime()
		self.day_format = '%s/%s/%s'%(curtime.tm_year,curtime.tm_mon,curtime.tm_mday)
		self.time_format = '%s:%s:%s'%(curtime.tm_hour,curtime.tm_min,curtime.tm_sec)
		self.tz_format = '0'
		return

	def set_date(self,date):
		self.day_format = date
		return True

	def set_time(self,timed):
		self.time_format = timed
		return True

	def set_tzoff(self,tz):
		self.tz_format = tz
		return True

	def value_format(self):
		s = ''
		if self.special_format is not None:
			s += self.special_format
		else:
			s += '%s %s %s'%(self.day_format,self.time_format,self.tz_format)
		return s

	def set_never(self):
		self.special_format = 'never'
		return True

	def set_epoch(self,epoch):
		self.special_format = 'epoch %s'%(epoch)
		return True

	def format_config(self,tabs=0):
		return self.value_format()

class PermitDeclaration(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		self.permit_format = 'ALL'
		self.mode = 'allow'
		return

	def set_after_date(self,datetime):
		self.permit_format = 'after %s'%(datetime)
		return True

	def set_members_of(self,member):
		self.permit_format = 'members of %s'%(member)
		return True

	def set_allow_mode(self,mode):
		self.permit_format = mode
		return True

	def set_mode(self,mode):
		self.mode=  mode
		return True

	def value_format(self):
		return self.permit_format

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += '%s %s;\n'%(self.mode,self.permit_format)
		return s

class Prefix6Statement(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		self.prefix_pair = []
		self.prefix_mask = ''
		self.mode = 'prefix6'
		return

	def set_ipv6_pair(self,ip1,ip2):
		self.prefix_pair = [ip1,ip2] 
		return True

	def set_mask(self,mask):
		self.prefix_mask = mask
		return True

	def value_format(self):
		s = ''
		s += '%s'%(self.mode)
		for c in self.prefix_pair:
			s += ' %s'%(c)
		s += ' /%s'%(self.prefix_mask)
		return s

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += self.value_format()
		s += ';\n'
		return s

class FixedPrefix6Statement(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		self.prefix_pair = []
		self.prefix_mask = ''
		self.mode = 'fixed-prefix6'
		return


	def set_ipv6(self,ip1):
		self.prefix_pair = [ip1] 
		return True

	def set_mask(self,mask):
		self.prefix_mask = mask
		return True

	def value_format(self):
		s = ''
		s += '%s'%(self.mode)
		for c in self.prefix_pair:
			s += ' %s'%(c)
		s += ' /%s'%(self.prefix_mask)
		return s

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += self.value_format()
		s += ';\n'
		return s

class AuthoritativeStatement(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		self.mode = ''
		return

	def value_format(self):
		return '%s authoritative'%(self.mode)

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += self.value_format()
		s += ';\n'
		return s

	def set_mode(self,mode):
		self.mode = mode
		return True

class ExprOpBase(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(self.__class__,self).__init__(typename,children,startelm,endelm)
		return

	def check_data_expr_op(self):
		return False

	def check_numeric_expr_op(self):
		return False

class ConstData(YaccDhcpObject):
	def __init__(self,value,startelm=None,endelm=None):
		typename = self.__class__.__name__
		children = []
		super(ConstData,self).__init__(typename,children,startelm,endelm)
		self.value = value
		return


	def set_value(self,value):
		self.value = value
		return

	def value_format(self):
		s = ''
		s = self.value
		if self.if_need_quoted(self.value):
			s = self.quoted_string(self.value)
		return s


class DDnsUpdateStyle(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(DDnsUpdateStyle,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			idx = 0
			for c in self.children:
				if idx > 0:
					s += ' '
				s += c.value_format()
				idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		if len(self.value_format()) > 0:
			s += ' ' * tabs * 4
			s += 'ddns-update-style %s;\n'%(self.value_format())
		return s


class DefaultLeaseTime(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(DefaultLeaseTime,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			idx = 0
			for c in self.children:
				if idx > 0:
					s += ' '
				s += c.value_format()
				idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		if len(self.value_format()) > 0:
			s += ' ' * tabs * 4
			s += 'default-lease-time %s;\n'%(self.value_format())
		return s

class PermitExec(YaccDhcpObject):
	def __init__(self,permit='allow',typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(PermitExec,self).__init__(typename,children,startelm,endelm)
		self.permit = permit
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			idx = 0
			for c in self.children:
				if idx > 0:
					s += ' '
				s += c.value_format()
				idx += 1
		return s


	def format_config(self,tabs=0):
		s = ''
		if len(self.value_format()) > 0:
			s += ' ' * tabs * 4
			s += '%s %s;\n'%(self.permit,self.value_format())
		return s


class AllowPermit(PermitExec):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		super(AllowPermit,self).__init__('allow',typename,children,startelm,endelm)
		return


class DenyPermit(PermitExec):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		super(DenyPermit,self).__init__('deny',typename,children,startelm,endelm)
		return


class IgnorePermit(PermitExec):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		super(IgnorePermit,self).__init__('ignore',typename,children,startelm,endelm)
		return

class ExprOp(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(ExprOp,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			idx = 0
			for c in self.children:
				if idx > 0:
					s += ' '
				s += c.value_format()
				idx += 1
		return s

class DomainName(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(DomainName,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			idx = 0
			for c in self.children:
				if idx > 0:
					s += ' '
				s += c.value_format()
				idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		if len(self.value_format()) > 0:
			s += ' ' * tabs * 4
			s += 'option domain-name %s;\n'%(self.value_format())
		return s

class DomainNameServers(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'DomainNameServers'
		super(DomainNameServers,self).__init__(typename,children,startelm,endelm)
		return


	def value_format(self):
		s = ''
		idx = 0
		for c in self.children:
			if idx > 0:
				s += ','
			s += c.value_format()
			idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'option domain-name-servers %s;\n'%(self.value_format())
		return s


class LogServers(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = 'LogServers'
		super(LogServers,self).__init__(typename,children,startelm,endelm)
		return


	def value_format(self):
		s = ''
		idx = 0
		for c in self.children:
			if idx > 0:
				s += ','
			s += c.value_format()
			idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'option log-servers %s;\n'%(self.value_format())
		return s

class MaxLeaseTime(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(MaxLeaseTime,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			idx = 0
			for c in self.children:
				if idx > 0:
					s += ' '
				s += c.value_format()
				idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		if len(self.value_format()) > 0:
			s += ' ' * tabs * 4
			s += 'max-lease-time %s;\n'%(self.value_format())
		return s


class LogFacility(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(LogFacility,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			idx = 0
			for c in self.children:
				if idx > 0:
					s += ' '
				s += c.value_format()
				idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		if len(self.value_format()) > 0:
			s += ' ' * tabs * 4
			s += 'log-facility %s;\n'%(self.value_format())
		return s

class SyslogValues(ConstData):
	def __init__(self,value,startelm=None,endelm=None):
		super(SyslogValues,self).__init__(value,startelm,endelm)
		valid_values = ['kern','user','mail','daemon','auth','syslog','lpr','news','uucp','cron','authpriv','ftp']
		for i in range(8):
			valid_values.append('local%d'%(i))
		if value not in valid_values:
			raise Exception('%s [%s] not valid type %s'%(self.location(),value,repr(valid_values)))
		return

class OptionFileName(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(OptionFileName,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			idx = 0
			for c in self.children:
				if idx > 0:
					s += ' '
				s += c.value_format()
				idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		if len(self.value_format()) > 0:
			s += ' ' * tabs * 4
			s += 'filename %s;\n'%(self.value_format())
		return s

class InterfaceName(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(InterfaceName,self).__init__(typename,children,startelm,endelm)
		self.interfacename = None
		return

	def value_format(self,tabs=0):
		s = ''
		if self.interfacename is not None:
			s += self.safe_quote_string(self.interfacename)
		return s


	def format_config(self,tabs=0):		
		return self.value_format()

	def start_interfacename(self,value):
		self.interfacename = value
		return

class InterfaceDeclaration(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(InterfaceDeclaration,self).__init__(typename,children,startelm,endelm)
		self.interface = ''
		return

	def value_format(self):
		s = ''
		s += self.safe_quote_string(self.interface)
		return s

	def set_interface(self,value):
		self.interface = value
		return

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'interface %s ;\n'%(self.interface)
		return s

class OptionNextServer(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(OptionNextServer,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		if len(self.children) > 0:
			idx = 0
			for c in self.children:
				if idx > 0:
					s += ' '
				s += c.value_format()
				idx += 1
		return s

	def format_config(self,tabs=0):
		s = ''
		if len(self.value_format()) > 0:
			s += ' ' * tabs * 4
			s += 'next-server %s;\n'%(self.value_format())
		return s

class SubnetDeclaration(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(SubnetDeclaration,self).__init__(typename,children,startelm,endelm)
		return

class OptionName(YaccDhcpObject):
	def __init__(self,name,startelm=None,endelm=None):
		typename = self.__class__.__name__
		super(OptionName,self).__init__(typename,None,startelm,endelm)
		self.name = name
		return

	def value_format(self):
		return '%s'%(self.name)

class OptionBase(YaccDhcpObject):
	def __init__(self,typename=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(OptionBase,self).__init__(typename,None,startelm,endelm)
		return


class HostIdentifierDeclaration(OptionBase):
	def __init__(self,typename=None,startelm=None,endelm=None):
		super(HostIdentifierDeclaration,self).__init__(typename,startelm,endelm)
		return


	def value_format(self):
		s = ''
		if len(self.children) > 0:
			for k in self.children:
				if len(s) > 0:
					s += ' '
				logging.info('k %s'%(repr(k)))
				s += '%s'%(k.value_format())
		return s

	def append_child(self,*args):
		for c in args:
			if isinstance(c,tuple) or isinstance(c,list):
				for ck in c:
					if isinstance(c,object) and getattr(c.__class__,'append_child',None) is not None:
						self.append_child(ck)
					else:
						logging.error('ck %s not ok'%(repr(ck)))
			elif isinstance(c,object) and issubclass(c.__class__,YaccDhcpObject):
				self.children.append(c)
			else:
				logging.error('c %s not ok'%(repr(c)))
		return

	def format_config(self,tabs=0):
		s = ''
		s += ' ' * tabs * 4
		s += 'host-identifier option '
		s += self.value_format()
		s += ';\n'
		return s


class OptionHandle(YaccDhcpObject):
	clsmap = {
		'host-identifier': 'HostIdentifierDeclaration',
		'dhcp6.client-id' : 'Dhcp6ClientId'
	}
	def __init__(self,typename=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(OptionHandle,self).__init__(typename,None,startelm,endelm)
		return

	def handle_option(self,clsname,startelm,endelm,*args):
		if not isinstance(clsname,object) or not issubclass(clsname.__class__,OptionName):
			raise Exception('not define option name baseclass [%s]'%(repr(clsname)))

		if clsname.value_format() not in self.__class__.clsmap.keys():
			raise Exception('[%s] not supported for Option Handle'%(clsname.value_format()))

		m = sys.modules[__name__]
		modcls = getattr(m,self.__class__.clsmap[clsname.value_format()],None)
		if modcls is None:
			raise Exception('can not find class [%s]'%(self.__class__.clsmap[clsname.value_format()]))
		newcls = modcls(None,startelm,endelm)
		if not issubclass(newcls.__class__,OptionBase):
			raise Exception('[%s] not OptionBase subclass'%(self.__class__.clsmap[clsname.value_format()]))
		newcls.append_child(*args)
		return newcls


class HostDeclarations(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(HostDeclarations,self).__init__(typename,children,startelm,endelm)
		return


class HardwareAddr(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(HardwareAddr,self).__init__(typename,children,startelm,endelm)
		self.hardwareaddr = None
		return

	def value_format(self):
		s = ''
		if self.hardwareaddr is not None:
			s = self.hardwareaddr
		return s

	def format_config(self,tabs=0):
		s = ''
		s += value_format()
		return s

	def start_addr(self,value):
		self.hardwareaddr = value
		return

	def append_colone_text(self,value):
		if self.hardwareaddr is None:
			raise Exception('not set hardwareaddr yet')
		self.hardwareaddr += ':'+value
		return

class HardwareStatement(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(HardwareStatement,self).__init__(typename,children,startelm,endelm)
		self.hard_type = None
		self.hard_addr = None
		return

	def value_format(self):
		s = ''
		if self.hard_type is not None:
			s += self.hard_type.value_format()

		if self.hard_addr is not None:
			if len(s) > 0:
				s += ' '
			s += self.hard_addr.value_format()
		return s

	def set_type(self,t):
		self.hard_type = t
		return

	def set_addr(self,v):
		self.hard_addr = v
		return

	def format_config(self,tabs=0):
		s = ' ' * tabs * 4
		s += 'hardware %s ;\n'%(self.value_format())
		return s

class HostDeclaration(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(HostDeclaration,self).__init__(typename,children,startelm,endelm)
		return

class ArgSpaceList(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(ArgSpaceList,self).__init__(typename,children,startelm,endelm)
		return

	def format_config(self,tabs=0):
		s = ''
		for c in self.children:
			if len(s) > 0:
				s += ' '
			s += c.value_format()
		return s

	def value_format(self):
		s = ''
		for c in self.children:
			if len(s) > 0:
				s += ' '
			s += c.value_format()
		return s

class OptionValue(YaccDhcpObject):
	def __init__(self,typename=None,children=None,startelm=None,endelm=None):
		if typename is None:
			typename = self.__class__.__name__
		super(OptionValue,self).__init__(typename,children,startelm,endelm)
		return

	def value_format(self):
		s = ''
		for c in self.children:
			if len(s) > 0:
				s += ' '
			s += c.value_format()
		return s

