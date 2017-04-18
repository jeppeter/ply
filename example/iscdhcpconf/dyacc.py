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
import dhcpconf


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

	def p_statements_empty(self,p):
		''' statements : empty
		'''
		statements = dhcpconf.Statements(None,None,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
		p[0] = statements
		if self.statements is not None:
			self.statements = None
		self.statements = statements
		p[1] = None
		return

	def p_statements_statement(self,p):
		'''statements : statements statement
		'''
		statements = dhcpconf.Statements()
		statements.extend_children(p[1].children)
		statements.append_child(p[2])
		statements.set_pos_by_children()
		p[1] = None
		if self.statements is not None:
			self.statements = None
		self.statements = statements
		return

	def p_statement_host_state(self,p):
		''' statement : host_statement
		'''
		children = []
		children.append(p[1])
		p[0] = dhcpconf.Statement(None,children,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
		p[1] = None
		return

	def p_statement_shared_network_state(self,p):
		''' statement : shared_network_statement
		'''
		children = []
		children.append(p[1])
		p[0] = dhcpconf.Statement(None,children,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
		p[1] = None
		return

	def p_statement_subnet_state(self,p):
		''' statement subnet_statement
		'''
		children = []
		children.append_child(p[1])
		p[0] = dhcpconf.Statement(None,children)
		p[0].set_pos_by_children()
		p[1] = None
		return

	def p_shared_network_statement(self,p):
		''' shared_network_statement : SHARED_NETWORK TEXT LBRACE shared_network_declarations RBRACE
				 | SHARED_NETWORK NUMBER LBRACE shared_network_declarations RBRACE
		'''
		children = []
		children.append(p[4])
		p[0] = dhcpconf.SharedNetwork(None,children,p.slice[1].startline,p.slice[1].startpos,p.slice[5].startpos,p.slice[5].endpos)
		p[0].set_shared_host(p.slice[2].value)
		p[4] = None
		return

	def p_shared_network_delcaration_empty(self,p):
		''' shared_network_declarations : empty
		'''
		children = []
		children.append(p[1])
		p[0] = dhcpconf.SharedNetworkDeclarations(None,children)
		p[0].set_pos_by_children()
		p[1] = None
		return

	def p_shared_network_declaration_combine(self,p):
		''' shared_network_declarations : shared_network_declarations interface_declaration
		           | shared_network_declarations statements
		'''
		p[1].append_child(p[2])
		p[1].set_pos_by_children()
		p[0] = p[1]
		p[1] = None
		p[2] = None
		return

	def p_interface_declarations(self,p):
		''' interface_declaration : INTERFACE interface_name SEMI
		'''
		p[0] = dhcpconf.InterfaceDeclaration(None,None,p.slice[1].startline,p.slice[1].startpos,p.slice[2].endline,p.slice[2].endpos)
		p[0].set_interface(p[2].value_format())
		return

	def p_interface_name(self,p):
		''' interface_name : TEXT
		'''
		p[0] = dhcpconf.InterfaceName(None,None,p.slice[1].startline,p.slice[1].startpos,p.slice[1].endline,p.slice[1].endpos)
		p[0].start_interfacename(p.slice[1].value)		
		return


	def p_host_statement(self,p):
		''' host_statement : HOST host_name LBRACE declarations RBRACE
		'''
		children = []
		# this is for declarations
		children.append(p[4])
		p[0] = dhcpconf.HostStatement(None,children,p.slice[1].startline,p.slice[1].startpos,p.slice[5].endline,p.slice[5].endpos) 
		p[0].set_hostname(p[2])
		p[2] = None
		p[4] = None
		return

	def p_host_name_empty(self,p):
		''' host_name : empty
		'''
		hostname = dhcpconf.HostName('',None,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
		p[0] = hostname
		p[1] = None
		return

	def p_host_name_ipaddr(self,p):
		''' host_name : ipaddr
			| dns_name
		'''		
		hostname = dhcpconf.HostName(p[1].value_format(),None,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
		p[0] = hostname
		p[1] = None
		return

	def p_dns_name(self,p):
		''' dns_name : dns_name DOT TEXT
		'''
		p[0] = dhcpconf.DnsName()
		return

	def p_declarations_empty(self,p):
		'''declarations : empty
		'''
		declarations = dhcpconf.Declarations(None,None,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
		p[0] = declarations
		p[1] = None
		return

	def p_declarations_declaration(self,p):
		''' declarations : declarations declaration
		'''
		declarations = dhcpconf.Declarations(None,None,p[1].startline,p[1].startpos,p[1].endline,p[1].endpos)
		declarations.extend_children(p[1].children)
		declarations.append_child(p[2])
		declarations.set_pos_by_children()
		p[0] = declarations
		p[1] = None
		return

	def p_declaration(self,p):
		''' declaration : hardware_declaration
				| fixed_address_declaration
		'''
		children = []
		children.append(p[1])
		p[0] = dhcpconf.Declaration(children)
		p[0].set_pos_by_children()
		return

	def p_hardware_declaration(self,p):
		''' hardware_declaration : HARDWARE hardware_type SEMI
		'''
		p[0] = p[2]
		return

	def p_hardware_type(self,p):
		''' hardware_type : ETHERNET macaddr
		'''
		p[2].check_valid_macaddr()
		hardwaretype = dhcpconf.HardwareType('ethernet',None,p.slice[1].startline,p.slice[1].startpos,p.slice[1].endline,p.slice[1].endpos)
		children = []
		children.append(hardwaretype)
		children.append(p[2])
		hardware = dhcpconf.HardwareDeclaration(children)
		hardware.set_pos_by_children()
		p[0] = hardware
		return

	def p_macaddr(self,p):
		''' macaddr : macaddr COLON TEXT
				| macaddr COLON NUMBER
				| TEXT
				| NUMBER
		'''
		if len(p) == 2:
			macobj = dhcpconf.MacAddress(p.slice[1].value,None,p.slice[1].startline,p.slice[1].startpos,p.slice[1].endline,p.slice[1].endpos)
		else:
			macobj = p[1]
			macobj.append_colon_part(p.slice[3].value,p.slice[3].endline,p.slice[3].endpos)
			p[1] = None
		p[0] = macobj
		return

	def p_error(self,p):
		raise Exception('find error %s'%(repr(p)))

	def p_fixed_address(self,p):
		''' fixed_address_declaration : FIXED_ADDRESS host_name SEMI
		'''
		p[0] = dhcpconf.FixedAddressDeclaration(p[2].value_format(),None,p.slice[1].startline,p.slice[1].startpos,p.slice[3].endline,p.slice[3].endpos)
		p[2] = None
		return

	def p_subnetstate(self,p):
		''' subnet_statement : SUBNET ipaddr NETMASK ipmask LBRACE subnet_declarations RBRACE
		'''
		children = []
		children.append(p[6])
		p[0] = dhcpconf.SubnetStatement(None,children,p.slice[1].startline,p.slice[1].startpos,p.slice[7].endline,p.slice[7].endpos)
		p[0].set_ipaddr(ipaddr)
		p[0].set_mask(ipmask)
		p[2] = None
		p[4] = None
		p[6] = None
		return

	def p_ipaddr(self,p):
		''' ipaddr : ipv4_addr
			| ipv6_addr
		'''
		p[1].check_valid_address()
		p[0] = p[1]
		p[1] = None
		return

	def p_ipv4_addr(self,p):
		''' ipv4_addr : NUMBER DOT NUMBER DOT NUMBER DOT NUMBER
		'''
		p[0] = dhcpconf.IpAddress(None,None,p.slice[1].startline,p.slice[1].startpos,p.slice[7].endline,p.slice[7].endpos)
		value = ''
		for i in range(4):
			if len(value) > 0:
				value += '.'
			value += '%s'%(p.slice[2*i+1].value)
		p[0].set_ipv4_address(value)
		return

	def p_ipv6_addr_colon_text(self,p):
		''' ipv6_addr :  ipv6_addr COLON TEXT
			 | ipv6_addr COLON NUMBER
		'''
		if len(p.slice[3].value) < 1 or len(p.slice[3].value) > 2:
			raise Exception('can not parse [%s:%s-%s:%s] %s'%(p.slice[3].startline,
				p.slice[3].startpos,p.slice[3].endline,p.slice[3].endpos,p.slice[3].value))
		p[0] = p[1]
		p[1] = None
		p[0].append_ipv6(p.slice[3].value,p.slice[3].endline,p.slice[3].endpos)
		return

	def p_ipv6_addr_colon(self,p):
		''' ipv6_addr : ipv6_addr COLON
		'''
		p[0] = p[1]
		p[0].append_ipv6_colon(p.slice[2].endline,p.slice[2].endpos)
		p[1] = None
		return

	def p_ipv6_addr_text(self,p):
		''' ipv6_addr : TEXT 
				| NUMBER
		'''
		p[0] = dhcpconf.IpAddress()
		p[0].start_ipv6_address(p.slice[1].value,p.slice[1].startline,p.slice[1].startpos,p.slice[1].endline,p.slice[1].endpos)
		return

	def p_ipmask(self,p):
		''' ipmask : ipv4_addr
			| ipv6_addr
		'''
		p[1].check_valid_mask()
		p[0] = p[1]
		p[1] = None
		return


	def p_empty(self,p):
		''' empty :		
		'''
		p[0] = dhcpconf.YaccDhcpObject('Empty',None,p.lexer.lineno,(p.lexer.lexpos-p.lexer.linepos),p.lexer.lineno,(p.lexer.lexpos-p.lexer.linepos))
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



