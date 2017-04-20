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
		p[0] = dhcpconf.Statements(None,None,p[1],p[1])
		p[1] = None
		if self.statements is not None:
			self.statements = None
		self.statements = p[0]
		return

	def p_statements_statement(self,p):
		'''statements : statements statement
		'''
		p[1].append_child(p[2])
		p[1].set_pos_by_children()
		p[0] = p[1]
		p[1] = None
		if self.statements is not None:
			self.statements = None
		self.statements = p[0]
		return

	def p_statement_multi(self,p):
		''' statement : include_statement
		     | host_statement
		     | group_statement
			 | shared_network_statement
			 | subnet_statement
			 | subnet6_statement
			 | vendor_class_statement
			 | user_class_statement
			 | class_statement
			 | subclass_statement
			 | option_statement
			 | pool_statement
			 | range_declaration
			 | prefix6_statement
			 | fixed_prefix6_statement
			 | authoritative_statement
			 | server_identifier_statement
		'''
		children = []
		children.append(p[1])
		p[0] = dhcpconf.Statement(None,children,p[1],p[1])
		p[1] = None
		return

	def p_include_statement(self,p):
		''' include_statement : INCLUDE TEXT SEMI
		'''
		p[0] = dhcpconf.IncludeStatement(None,None,p.slice[1],p.slice[3])
		p[0].set_file(p.slice[2].value)
		return

	def p_server_identifier_statement(self,p):
		''' server_identifier_statement : SERVER_IDENTIFIER option_values SEMI
		'''
		p[0] = dhcpconf.ServerIdentifier(None,None,p.slice[1],p.slice[3])
		p[0].append_child(p[2])
		p[2] = None
		return

	def p_shared_network_statement(self,p):
		''' shared_network_statement : SHARED_NETWORK host_name LBRACE shared_network_declarations RBRACE
		'''
		children = []
		children.append(p[4])
		p[0] = dhcpconf.SharedNetwork(None,children,p.slice[1],p.slice[5])
		p[0].set_shared_host(p[2])
		p[4] = None
		return

	def p_shared_network_delcarations(self,p):
		''' shared_network_declarations : empty
		         | shared_network_declarations shared_network_declaration
		'''
		if len(p) == 2:
			p[0] = dhcpconf.SharedNetworkDeclarations(None,None,p[1],p[1])
			p[1] = None
		else:
			p[0] = p[1]
			p[0].append_child(p[2])
			p[0].set_pos_by_children()
			p[1] = None
			p[2] = None
		return

	def p_shared_network_declaration(self,p):
		''' shared_network_declaration : interface_declaration
		           | statements
		'''
		p[0] = dhcpconf.SharedNetworkDeclaration()
		p[0].append_child(p[1])
		p[0].set_pos_by_children()
		p[1] = None
		return

	def p_group_statement(self,p):
		'''group_statement : GROUP TEXT LBRACE group_declarations RBRACE
		'''
		p[0] = dhcpconf.GroupStatement(None,None,p.slice[1],p.slice[5])
		p[0].set_groupname(p.slice[2].value)
		p[0].append_child(p[4])
		p[4] = None
		return

	def p_group_declarations(self,p):
		''' group_declarations : empty
		             | group_declarations group_declaration
		'''
		if len(p) == 2:
			p[0] =dhcpconf.GropuDeclarations(None,None,p[1],p[1])
			p[1] = None
		else:
			p[0] = p[1]
			p[0].append_child(p[2])
			p[0].set_pos_by_children()
			p[1] = None
			p[2] = None
		return

	def p_group_declaraion(self,p):
		''' group_declaration : deleted_declaration
		          | dynamic_declaration
		          | static_declaraion
		          | statements
		'''
		p[0] = dhcpconf.GroupDeclaration()
		p[0].append_child(p[1])
		p[0].set_pos_by_children()
		p[1] = None
		return


	def p_dynamic_declaration(self,p):
		''' dynamic_declaration : DYNAMIC SEMI
		'''
		p[0] = dhcpconf.DynamicDeclaration(None,None,p.slice[1],p.slice[2])
		return

	def p_static_declaration(self,p):
		''' static_declaration : STATIC SEMI
		'''
		p[0] = dhcpconf.StaticDeclaration(None,None,p.slice[1],p.slice[2])
		return

	def p_interface_declaration(self,p):
		''' interface_declaration : INTERFACE interface_name SEMI
		'''
		p[0] = dhcpconf.InterfaceDeclaration(None,None,p.slice[1],p.slice[3])
		p[0].set_interface(p[2])
		return

	def p_interface_name(self,p):
		''' interface_name : TEXT
		'''
		p[0] = dhcpconf.InterfaceName(None,None,p.slice[1],p.slice[1])
		p[0].start_interfacename(p.slice[1].value)
		return

	def p_option_routers(self,p):
		''' option_statement : OPTION ROUTERS host_name SEMI
		'''
		p[0] = dhcpconf.OptionRouters(None,p.slice[1],p.slice[4])
		p[0].set_routername(p[3])
		p[3] = None
		return

	def p_option_statement_space(self,p):
		''' option_statement : option_space_decl
		'''
		children = []
		children.append(p[1])
		p[0] = dhcpconf.OptionStatement()
		p[0].append_child(p[1])
		p[0].set_pos_by_children()
		p[1] = None
		return

	def p_option_space_decl(self,p):
		''' option_space_decl : OPTION SPACE TEXT option_space_declarations SEMI
		'''
		children = []
		children.append(p[4])
		p[0] = dhcpconf.OptionSpace(None,children,p.slice[1],p.slice[5])
		p[0].set_identify(p.slice[3].value)
		p[4] = None
		return

	def p_option_space_decl_empty(self,p):
		''' option_space_declarations : empty
		'''
		p[0] = dhcpconf.OptionSpaceDeclarations(None,None,p[1],p[1])
		p[1] = None
		return

	def p_option_space_decl_recur(self,p):
		''' option_space_declarations : option_space_declarations option_space_declaration
		'''
		p[1].append_child(p[2])
		p[1].set_pos_by_children()
		p[0] = p[1]
		p[1] = None
		p[2] = None
		return

	def p_option_space_declaration_code(self,p):
		''' option_space_declaration : CODE WIDTH NUMBER
		'''
		p[0] = dhcpconf.OptionSpaceDeclaration(None,None,p.slice[1],p.slice[3])
		p[0].set_code(p.slice[3].value)
		return

	def p_option_space_declaration_length(self,p):
		''' option_space_declaration : LENGTH WIDTH NUMBER
		'''
		p[0] = dhcpconf.OptionSpaceDeclaration(None,None,p.slice[1],p.slice[3])
		p[0].set_length(p.slice[3].value)
		return

	def p_option_space_declaration_hash(self,p):
		''' option_space_declaration : HASH SIZE NUMBER
		'''
		p[0] = dhcpconf.OptionSpaceDeclaration(None,None,p.slice[1],p.slice[3])
		p[0].set_hash(p.slice[3].value)
		return

	def p_option_name_value(self,p):
		''' option_statement : option_name_value 
		'''
		p[0] = dhcpconf.OptionStatement()
		p[0].append_child(p[1])
		p[0].set_pos_by_children()
		p[1] = None
		return

	def p_option_name_value_detail(self,p):
		''' option_name_value : OPTION option_name option_values SEMI
		'''
		p[0] = dhcpconf.OptionNameValue(None,None,p.slice[1],p.slice[4])
		p[0].set_name(p[2])
		p[0].set_value(p[3])
		p[2] = None
		p[3] = None
		return

	def p_option_name(self,p):
		''' option_name : TEXT
			   | TEXT DOT TEXT
		'''
		if len(p) == 2:
			p[0] = dhcpconf.OptionName(None,None,p.slice[1],p.slice[1])
			p[0].set_name(p.slice[1].value)
		else:
			p[0] = dhcpconf.OptionName(None,None,p.slice[1],p.slice[3])
			value = '%s.%s'%(p.slice[1].value,p.slice[3].value)
			p[0].set_name(value)
		return

	def p_option_values_recur(self,p):
		''' option_values : option_values option_value
		         | option_value
		'''
		if len(p) == 3:
			p[1].append_child(p[2])
			p[1].set_pos_by_children()
			p[0] = p[1]
			p[1] = None
			p[2] = None
		else:
			p[0] = dhcpconf.OptionValues()
			p[0].append_child(p[1])
			p[0].set_pos_by_children()
			p[1] = None
		return

	def p_option_value_code(self,p):
		''' option_value : CODE NUMBER EQUAL option_code_clauses
		'''
		p[0] = dhcpconf.OptionValue(None,None,p.slice[1],p[4])
		p[0].set_code_child(p.slice[2].value,p[4])
		p[4] = None
		return

	def p_option_value_equal(self,p):
		''' option_value : EQUAL data_expression_op
		'''
		p[0] = dhcpconf.OptionValue(None,None,p.slice[1],p[2])
		p[0].set_equal_child(p[2])
		p[2] = None
		return

	def p_option_value_data(self,p):
		''' option_value : option_data
		'''
		p[0] = dhcpconf.OptionValue(None,None,p[1],p[1])
		p[0].set_data_child(p[1])
		p[1] = None
		return

	def p_option_value_empty(self,p):
		''' option_value : empty
		'''
		p[0] = dhcpconf.OptionValue(None,None,p[1],p[1])
		p[1] = None
		return

	def p_option_code_clauses_empty(self,p):
		''' option_code_clauses : empty
		'''
		p[0] = dhcpconf.OptionCodeClauses(None,None,p[1],p[1])
		p[1] = None
		return

	def p_option_code_clauses_recur(self,p):
		''' option_code_clauses : option_code_clauses option_code_clause
		'''
		p[1].append_child(p[2])
		p[1].set_pos_by_children()
		p[0] = p[1]
		p[1] = None
		p[2] = None
		return

	def p_option_code_clause_ocsd_type(self,p):
		''' option_code_clause : ocsd_type
		'''
		p[0] = dhcpconf.OptionCodeClause(None,None,p[1],p[1])
		p[0].append_child(p[1])
		p[1] = None
		return

	def p_option_code_clause_ocsd_type_sequence(self,p):
		'''option_code_clause  : ocsd_type_sequence
		'''
		p[0] = dhcpconf.OptionCodeClause(None,None,p[1],p[1])
		p[0].append_child(p[1])
		p[1] = None
		return

	def p_option_code_clause_ocsd_simple_type_sequence(self,p):
		'''option_code_clause : ARRAY OF ocsd_simple_type_sequence
		'''
		p[0] = dhcpconf.OptionCodeClause(None,None,p.slice[1],p[3])
		p[0].append_array_child(p[3])
		p[1] = None
		return

	def p_ocsd_type_sequence(self,p):
		''' ocsd_type_sequence : LBRACE ocsd_types RBRACE
		'''
		p[0] = dhcpconf.OptionCodeSequence(None,None,p.slice[1],p.slice[3])
		p[0].append_child(p[2])
		p[1] = None
		return

	def p_ocsd_types(self,p):
		''' ocsd_types : ocsd_type
				| ocsd_types ocsd_type
		'''
		if len(p) == 2:
			p[0] = dhcpconf.OptionCodeSimpleTypes(None,None)
			p[0].append_child(p[1])
			p[0].set_pos_by_children()
			p[1] = None
		else:
			p[0] = p[1]
			p[0].append_child(p[2])
			p[0].set_pos_by_children()
			p[1] = None
			p[2] = None
		return

	def p_ocsd_type(self,p):
		''' ocsd_type : ocsd_simple_type
		        | ARRAY OF ocsd_simple_type
		'''
		if len(p) == 2:
			p[0] = dhcpconf.OptionCodeSimpleType(None,None,p[1],p[1])
			p[0].append_child(p[1])
			p[1] = None
		else:
			p[0] = dhcpconf.OptionCodeSimpleType(None,None,p.slice[1],p[3])
			p[0].append_array_child(p[3])
			p[3] = None
		return
	def p_ocsd_simple_types(self,p):
		'''ocsd_simple_types : ocsd_simple_type
		      | ocsd_simple_types ocsd_simple_type
		'''
		if len(p) == 2:
			p[0] = dhcpconf.OptionCodeSimpleDeclareTypes()
			p[0].append_child(p[1])
			p[0].set_pos_by_children()
			p[1] = None
		else:
			p[0] = p[1]
			p[0].append_child(p[2])
			p[0].set_pos_by_children()
			p[1] = None
			p[2] = None
		return

	def p_ocsd_simple_type_boolean(self,p):
		''' ocsd_simple_type : BOOLEAN 
		         | TOKEN_TEXT
		         | IP_ADDRESS
		         | ZEROLEN
		'''
		p[0] = dhcpconf.OptionCodeSimpleDeclareType(None,None,p.slice[1],p.slice[1])
		p[0].set_type_name(p.slice[1].value)
		return

	def p_ocsd_simple_type_number(self,p):
		''' ocsd_simple_type : INTEGER NUMBER 
		         | SIGNED INTEGER NUMBER
		         | UNSIGNED INTEGER NUMBER
		'''
		if len(p) == 3:
			p[0] = dhcpconf.OptionCodeSimpleDeclareType(None,None,p.slice[1],p.slice[2])
			p[0].set_type_name('integer')
			p[0].set_number(p.slice[2].value)
		elif len(p) == 4:
			p[0] = dhcpconf.OptionCodeSimpleDeclareType(None,None,p.slice[1],p.slice[3])
			typename = '%s %s'%(p.slice[1].value,p.slice[2].value)
			p[0].set_type_name(typename)
			p[0].set_number(p.slice[3].value)
		return

	def p_ocsd_simple_type_text(self,p):
		''' ocsd_simple_type : TEXT 
		          | ENCAPSULATE TEXT
		'''
		if len(p) == 2:
			p[0] = dhcpconf.OptionCodeSimpleDeclareType(None,None,p.slice[1],p.slice[1])
			p[0].set_text(p.slice[1].value)
		else:
			p[0] = dhcpconf.OptionCodeSimpleDeclareType(None,None,p.slice[1],p.slice[2])
			p[0].set_type_name('encapsulate')
			p[0].set_text(p.slice[2].value)
		return


	def p_host_statement(self,p):
		''' host_statement : HOST host_name LBRACE host_declarations RBRACE
		'''
		children = []
		# this is for declarations
		children.append(p[4])
		p[0] = dhcpconf.HostStatement(None,children,p.slice[1],p.slice[5])
		p[0].set_hostname(p[2])
		p[2] = None
		p[4] = None
		return

	  # we do not make this ok for not colon handle
	# def p_host_name_colon_text(self,p):
	# 	''' host_name : host_name COLON TEXT
	# 		| host_name COLON NUMBER
	# 	'''		
	# 	p[0] = p[1]
	# 	p[0].append_colone_text(p.slice[3].value,p.slice[3])
	# 	p[1] = None
	# 	return

	def p_host_name_dot_text(self,p):
		''' host_name : host_name DOT TEXT
			| host_name DOT NUMBER
			| host_name DOT
		'''
		p[0] = p[1]
		if len(p) == 3:
			p[0].append_dot_text(p.slice[3].value,p.slice[3])		
			p[1] = None
		else:
			p[0].append_dot(p.slice[2])
		return

	def p_host_name_text(self,p):
		''' host_name : TEXT
			| NUMBER
		'''
		p[0] = dhcpconf.HostName(None,p.slice[1],p.slice[1])
		p[0].start_hostname(p.slice[1].value)
		return



	def p_dns_name(self,p):
		''' dns_name : dns_name DOT TEXT
		'''
		p[0] = p[1]
		p[0].append_dot_name(p.slice[3].value,p.slice[3])
		p[1] = None
		return

	def p_dns_name_text(self,p):
		''' dns_name : TEXT 
		'''
		p[0] = dhcpconf.DnsName(None,None,p.slice[1],p.slice[1])
		p[0].start_dnsname(p.slice[1].value)
		return

	def p_host_declarations_empty(self,p):
		'''host_declarations : empty
		'''
		declarations = dhcpconf.HostDeclarations(None,None,p[1],p[1])
		p[0] = declarations
		p[1] = None
		return

	def p_host_declarations_declaration(self,p):
		''' host_declarations : host_declarations host_declaration
		'''
		p[0] = p[1]
		p[0].append_child(p[2])
		p[0].set_pos_by_children()
		p[1] = None
		p[2] = None
		return

	def p_prefix6_statement(self,p):
		''' prefix6_statement : PREFIX6 ipv6_addr ipv6_addr SLASH NUMBER SEMI
		'''
		p[0] = dhcpconf.Prefix6Statement(None,None,p.slice[1],p.slice[6])
		p[0].set_ipv6_pair(p[2].value_format(),p[3].value_format())
		p[0].set_mask(p.slice[5].value)
		p[2] = None
		p[3] = None
		return

	def p_fixed_prefix6_statement(self,p):
		''' fixed_prefix6_statement : FIXED_PREFIX6 ipv6_addr SLASH NUMBER SEMI
		'''
		p[0] = dhcpconf.FixedPrefix6Statement(None,None,p.slice[1],p.slice[5])
		p[0].set_ipv6(p[2].value_format())
		p[0].set_mask(p.slice[4].value)
		p[2] = None
		return


	def p_host_declaration(self,p):
		''' host_declaration : dynamic_declaration				
				| deleted_declaration
				| uid_statement
				| host_identifier_declaration
		        | hardware_statement
				| fixed_address_declaration
				| host_group_declaration
				| statements

		'''
		children = []
		children.append(p[1])
		p[0] = dhcpconf.HostDeclaration(children)
		p[0].set_pos_by_children()
		p[1] = None
		return


	def p_deleted_declaration(self,p):
		''' deleted_declaration : DELETED SEMI
		'''
		p[0] = dhcpconf.DeletedDeclaration(None,None,p.slice[1],p.slice[2])
		return

	def p_host_group_declaration(self,p):
		''' host_group_declaration : GROUP TEXT  SEMI
		'''
		p[0] = dhcpconf.HostGroupDeclaration(None,None,p.slice[1],p.slice[3])
		p[0].set_groupname(p.slice[2].value)
		return

	def p_uid_statement(self,p):
		''' uid_statement : UID uid_data SEMI
		'''
		bval = p[2].verify_uid_data()
		if not bval:
			raise Exception('not valid uid [%s] %s'%(p[2].location(),p[2].value_format()))
		p[0] = dhcpconf.UidStatement(None,None,p.slice[1],p.slice[3])
		p[0].set_uid(p[2])
		p[2] = None
		return

	def p_uid_data(self,p):
		''' uid_data : TEXT
		          | NUMBER
		          | uid_data COLON TEXT
		          | uid_data COLON NUMBER
		'''
		if len(p) == 2:
			p[0] = dhcpconf.UidData(None,None,p.slice[1],p.slice[1])
			p[0].append_text(p.slice[1].value)
		else:
			p[0] = p[1]
			p[0].append_colone_text(p.slice[3].value)
			p[1] = None
		return

	def p_host_identifier_declaration(self,p):
		''' host_identifier_declaration : HOST_IDENTIFIER OPTION option_name option_values SEMI
		'''
		p[0] = dhcpconf.HostIdentifierDeclaration(None,None,p.slice[1],p.slice[5])
		p[0].set_key_value(p[3],p[4])
		p[3] = None
		p[4] = None
		return

	def p_hardware_statement(self,p):
		''' hardware_statement : HARDWARE hardware_type SEMI
				| HARDWARE hardware_type hardware_addr SEMI
		'''
		if len(p) == 3:
			p[0] = dhcpconf.HardwareStatement(None,None,p.slice[1],p.slice[3])
			p[0].set_type(p[2])
		else:
			p[0] = dhcpconf.HardwareStatement(None,None,p.slice[1],p.slice[4])
			p[0].set_type(p[2])
			p[0].set_addr(p[3])		
		return

	def p_hardware_type(self,p):
		''' hardware_type : ETHERNET
		       | TOKEN_RING
		       | TOKEN_FDDI
		       | TOKEN_INFINIBAND
		       | TEXT
		'''
		p[0] = dhcpconf.HardwareType(None,None,p.slice[1],p.slice[1])
		p[0].set_type(p.slice[1].value)
		return

	def p_hardware_addr(self,p):
		''' hardware_addr : hardware_addr COLON TEXT
				| hardware_addr COLON NUMBER
				| TEXT
				| NUMBER
		'''
		if len(p) == 2:
			macobj = dhcpconf.HardwareAddr(p.slice[1].value,None,p.slice[1],p.slice[1])
		else:
			macobj = p[1]
			macobj.append_colon_part(p.slice[3].value,p.slice[3])
			p[1] = None
		p[0] = macobj
		return

	def p_error(self,p):
		raise Exception('find error %s'%(repr(p)))

	def p_fixed_address(self,p):
		''' fixed_address_declaration : FIXED_ADDRESS host_name SEMI
		'''
		p[0] = dhcpconf.FixedAddressDeclaration(p[2].value_format(),None,p.slice[1],p.slice[3])
		p[2] = None
		return

	def p_subnet_statement(self,p):
		''' subnet_statement : SUBNET ipv4_addr NETMASK ipv4_addr LBRACE subnet_declarations RBRACE
		'''
		children = []
		children.append(p[6])
		p[0] = dhcpconf.SubnetStatement(None,children,p.slice[1],p.slice[7])
		p[0].set_ipaddr(p[2])
		p[0].set_mask(p[4])
		p[2] = None
		p[4] = None
		p[6] = None
		return

	def p_subnet6_statement(self,p):
		''' subnet6_statement : SUBNET6 ipv6_addr SLASH NUMBER LBRACE subnet_declarations BRACE
		'''
		children = []
		children.append(p[6])
		p[0] = dhcpconf.Subnet6Statement(None,children,p.slice[1],p.slice[7])
		p[0].set_ipaddr6(p[2])
		p[0].set_netmask6(p.slice[4].value)
		return

	def p_subnet_delcarations(self,p):
		''' subnet_declarations : empty
				| subnet_declarations subnet_declaration
		'''
		if len(p) == 2:
			p[0] = dhcpconf.SubnetDeclarations(None,None,p[1],p[1])
			p[1] = None
		else:
			p[0] = p[1]
			p[0].append_child(p[2])
			p[0].set_pos_by_children()
			p[1] = None
			p[2] = None
		return

	def p_subnet_declaration(self,p):
		''' subnet_declaration : interface_declaration
		           | statements
		'''
		p[0] = dhcpconf.SubnetDeclaration()
		p[0].append_child(p[1])
		p[0].set_pos_by_children()
		p[1] = None
		return

	def p_vendor_class_statement(self,p):
		''' vendor_class_statement : VENDOR_CLASS class_name LBRACE class_declarations RBRACE
		'''
		p[0] = dhcpconf.VendorClassStatement(None,None,p.slice[1],p.slice[5])
		p[0].set_classname(p[2])
		p[0].append_child(p[4])
		p[2] = None
		p[4] = None
		return

	def p_user_class_statement(self,p):
		''' user_class_statement : USER_CLASS class_name LBRACE class_declarations RBRACE
		'''
		p[0] = dhcpconf.UserClassStatement(None,None,p.slice[1],p.slice[5])
		p[0].set_classname(p[2])
		p[0].append_child(p[4])
		p[2] = None
		p[4] = None
		return

	def p_class_statement(self,p):
		''' class_statement : CLASS class_name LBRACE class_declarations RBRACE
		'''
		p[0] = dhcpconf.ClassStatement(None,None,p.slice[1],p.slice[5])
		p[0].set_classname(p[2])
		p[0].append_child(p[4])
		p[2] = None
		p[4] = None
		return

	def p_subclass_statement(self,p):
		''' subclass_statement : SUBCLASS class_name LBRACE class_declarations RBRACE
		         | SUBCLASS class_name class_name LBRACE class_declarations RBRACE
		'''
		if len(p) == 5:
			p[0] = dhcpconf.SubClassStatement(None,None,p.slice[1],p.slice[5])
			p[0].set_classname(p[2])
			p[0.append_child(p[4])]
			p[2] = None
			p[4] = None
		else:
			p[0] = dhcpconf.SubClassStatement(None,None,p.slice[1],p.slice[6])
			p[0].set_classname(p[2])
			p[0].set_parentclass(p[3])
			p[0].append_child(p[5])
			p[2] = None
			p[3] = None
			p[5] = None
		return

	def p_class_name(self,p):
		''' class_name : TEXT
		'''
		p[0] = dhcpconf.ClassName(None,None,p.slice[1],p.slice[1])
		p[0].set_name(p.slice[1].value)
		return

	def p_class_declarations(self,p):
		''' class_declarations : empty
		        | class_declarations class_declaration
		'''
		if len(p) == 2:
			p[0] = dhcpconf.ClassDeclartions(None,None,p[1],p[1])
		else:
			p[0] = p[1].append_child_and_set_pos(p[2])
			p[1] = None
			p[2] = None
		return

	def p_class_declaration(self,p):
		''' class_declaration : dynamic_declaration
		           | deleted_declaration
		           | class_match_declaration
		           | class_spawn_declaration
		           | class_lease_declaration
		           | statements
		'''
		p[0] = dhcpconf.ClassDeclaration()
		p[0].append_child_and_set_pos(p[1])
		p[1] = None
		return

	def p_class_match_declaration(self,p):
		''' class_match_declaration : class_match_if_declaration
		          | class_match_sub_declaration
		'''
		p[0] = dhcpconf.ClassMatchDeclaration(None,None,p[1],p[1])
		p[0].append_child(p[1])
		p[1] = None
		return

	def p_class_match_if_declaration(self,p):
		''' class_match_if_declaration : MATCH IF boolean_expr_op SEMI
		'''
		p[0] = dhcpconf.ClassMatchIfDeclaration(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_class_match_sub_declaration(self,p):
		''' class_match_sub_declaration : MATCH data_expr_op SEMI
		'''
		p[0] = dhcpconf.ClassMatchSubDeclaration(None,None,p.slice[1],p.slice[3])
		p[0].append_child(p[2])
		p[2] = None
		return

	def p_class_spawn_declaration(self,p):
		''' class_spawn_declaration : SPAWN WIDTH data_expr_op SEMI
		'''
		p[0] = dhcpconf.ClassSpawnDeclaration(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_class_lease_declaration(self,p):
		''' class_lease_declaration : LEASE SEMI
		         | LEASE LIMIT NUMBER SEMI
		'''
		if len(p) == 3:
			p[0] = dhcpconf.ClassLeaseDeclaration(None,None,p.slice[1],p.slice[2])
		else:
			p[0] = dhcpconf.ClassLeaseDeclaration(None,None,p.slice[1],p.slice[4])
			p[0].set_limit(p.slice[3].value)
		return

	def p_authoritative_statement(self,p):
		'''authoritative_statement : NOT AUTHORITATIVE SEMI
		         | AUTHORITATIVE SEMI
		'''
		if len(p) == 4:
			p[0] = dhcpconf.AuthoritativeStatement(None,None,p.slice[1],p.slice[3])
			p[0].set_mode('not')
		else:
			p[0] = dhcpconf.AuthoritativeStatement(None,None,p.slice[1],p.slice[2])
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
		p[0] = dhcpconf.IpAddress(None,None,p.slice[1],p.slice[7])
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
		if len(p.slice[3].value) < 1 or len(p.slice[3].value) > 4:
			raise Exception('can not parse [%s:%s-%s:%s] %s'%(p.slice[3].startline,
				p.slice[3].startpos,p.slice[3].endline,p.slice[3].endpos,p.slice[3].value))
		p[0] = p[1]
		p[1] = None
		p[0].append_ipv6(p.slice[3].value,p.slice[3])
		return

	def p_ipv6_addr_colon(self,p):
		''' ipv6_addr : ipv6_addr COLON
		'''
		p[0] = p[1]
		p[0].append_ipv6_colon(p.slice[2])
		p[1] = None
		return

	def p_ipv6_addr_text(self,p):
		''' ipv6_addr : TEXT 
				| NUMBER
		'''
		p[0] = dhcpconf.IpAddress()
		p[0].start_ipv6_address(p.slice[1].value,p.slice[1],p.slice[1])
		return

	def p_ipmask(self,p):
		''' ipmask : ipv4_addr
			| ipv6_addr
		'''
		p[1].check_valid_mask()
		p[0] = p[1]
		p[1] = None
		return

	def p_pool_statement(self,p):
		''' pool_statement : POOL LBRACE pool_declarations RBRACE
		'''
		children = []
		children.append(p[3])
		p[0] = dhcpconf.PoolStatement(None,children,p.slice[1],p.slice[4])
		p[3] = None
		return

	def p_pool_declarations_empty(self,p):
		''' pool_declarations : empty
		'''
		p[0] = dhcpconf.PoolDeclarations(None,None)
		p[0].append_child(p[1])
		p[0].set_pos_by_children()
		p[1] = None
		return

	def p_pool_declarations_recursive(self,p):
		'''pool_declarations : pool_declarations pool_declaration
		'''
		p[0] = p[1]
		p[1] = None
		p[0].append_child(p[2])
		p[0].set_pos_by_children()
		p[2] = None
		return


	def p_pool_declaration_no_failover(self,p):
		''' pool_declaration : NO FAILOVER PEER SEMI
		'''
		p[0] = dhcpconf.Failover(None,None,p.slice[1],p.slice[4])
		p[0].set_no_failover()
		return

	def p_pool_declaration_failover_peer(self,p):
		''' pool_declaration : FAILOVER PEER dns_name SEMI
		'''
		p[0] = dhcpconf.Failover(None,None,p.slice[1],p.slice[4])
		p[0].set_failover(p[3].value_format())
		p[3] = None
		return

	def p_pool_declaration_range_declaration(self,p):
		'''pool_declaration : range_declaration
		'''
		p[0] = p[1]
		p[1] = None
		return

	def p_range_declaration_two(self,p):
		'''range_declaration : RANGE ipaddr ipaddr SEMI
		         | RANGE6 ipaddr ipaddr SEMI
		'''
		p[0] = dhcpconf.IpRange(None,None,p.slice[1],p.slice[4])
		p[0].set_mode(p.slice[1].value)
		p[0].set_range_ips(p[2].value_format(),p[3].value_format())
		p[2] = None
		p[3] = None
		return

	def p_range_declaration_one(self,p):
		'''range_declaration : RANGE ipaddr SEMI
		       | RANGE6 ipaddr SEMI
		'''
		p[0] = dhcpconf.IpRange(None,None,p.slice[1],p.slice[3])
		p[0].set_mode(p.slice[1].value)
		p[0].set_range_ips(p[2].value_format(),p[2].value_format())
		p[2] = None
		return


	def p_range_declaration_part(self,p):
		'''range_declaration : RANGE DYNAMIC_BOOTP ipaddr ipaddr SEMI
			| RANGE DYNAMIC_BOOTP ipaddr SEMI
			| RANGE6 DYNAMIC_BOOTP ipaddr ipaddr SEMI
			| RANGE6 DYNAMIC_BOOTP ipaddr SEMI
		'''
		if len(p) == 5:
			p[0] = dhcpconf.IpRange(None,None,p.slice[1],p.slice[4])
			p[3] = None
		else:
			p[0] = dhcpconf.IpRange(None,None,p.slice[1],p.slice[5])
			p[3] = None
			p[4] = None
		p[0].set_mode(p.slice[1].value)
		p[0].set_dynamic()
		return

	def p_pool_declaration_allow(self,p):
		'''pool_declaration : permit_declaration
		'''
		p[0] = p[1]
		p[1] = None
		return

	def p_permit_declaration_one_word(self,p):
		'''permit_declaration : ALLOW UNKNOWN SEMI
			 | ALLOW KNOWN_CLIENTS SEMI
			 | ALLOW UNKNOWN_CLIENTS SEMI
			 | ALLOW KNOWN SEMI
			 | ALLOW AUTHENTICATED SEMI
			 | ALLOW UNAUTHENTICATED SEMI
			 | ALLOW ALL SEMI
			 | DENY UNKNOWN SEMI
			 | DENY KNOWN_CLIENTS SEMI
			 | DENY UNKNOWN_CLIENTS SEMI
			 | DENY KNOWN SEMI
			 | DENY AUTHENTICATED SEMI
			 | DENY UNAUTHENTICATED SEMI
			 | DENY ALL SEMI
		'''
		typename = 'Allow'
		if p.slice[1].value == 'deny':
			typename = 'Deny'
		p[0] = dhcpconf.PermitDeclaration(typename,None,p.slice[1],p.slice[3])
		p[0].set_mode(p.slice[1].value)
		p[0].set_permit_mode(p.slice[2].value)
		return

	def p_permit_declaration_dynamic(self,p):
		''' permit_declaration : ALLOW DYNAMIC BOOTP SEMI
		          | DENY DYNAMIC BOOTP SEMI
		'''
		typename = 'Allow'
		if p.slice[1].value == 'deny':
			typename = 'Deny'
		p[0] = dhcpconf.PermitDeclaration(typename,None,p.slice[1],p.slice[4])
		p[0].set_mode(p.slice[1].value)
		p[0].set_permit_mode('dynamic bootp')
		return

	def p_permit_declaration_date_after(self,p):
		'''permit_declaration : ALLOW AFTER date_format SEMI
		         | DENY AFTER date_format SEMI
		'''
		typename = 'Allow'
		if p.slice[1].value == 'deny':
			typename = 'Deny'
		p[0] = dhcpconf.PermitDeclaration(typename,None,p.slice[1],p.slice[4])
		p[0].set_mode(p.slice[1].value)
		p[0].set_after_date(p[3].value_format())
		return

	def p_permit_declaration_members_of(self,p):
		''' permit_declaration : ALLOW MEMBERS OF TEXT SEMI
		        | DENY MEMBERS OF TEXT SEMI
		'''
		typename = 'Allow'
		if p.slice[1].value == 'deny':
			typename = 'Deny'
		p[0] = dhcpconf.PermitDeclaration(typename,None,p.slice[1],p.slice[5])
		p[0].set_mode(p.slice[1].value)
		p[0].set_members_of(p.slice[4].value)
		return


	def p_date_format_never(self,p):
		''' date_format : NEVER
		'''
		p[0] = dhcpconf.DateFormat(None,None,p.slice[1],p.slice[1])
		p[0].set_never()
		return

	def p_date_format_epoch(self,p):
		''' date_format : EPOCH NUMBER
		'''
		p[0] = dhcpconf.DateFormat(None,None,p.slice[1],p.slice[1])
		p[0].set_epoch(p.slice[2].value)
		return

	def p_date_format_yeardate(self,p):
		''' date_format : day_format time_format
			|  day_format time_format PLUS NUMBER
			|  day_format time_format MINUS NUMBER
		'''
		if len(p) == 3:
			p[0] = dhcpconf.DateFormat(None,None,p[1],p[2])
		elif len(p) == 5:
			p[0] = dhcpconf.DateFormat(None,None,p[1],p.slice[4])
		else:
			raise Exception('unknown date_format')
		p[0].set_date(p[1].value_format())
		p[0].set_time(p[2].value_format())
		if len(p) == 3:
			p[0].set_tzoff('0')
		elif len(p) == 5:
			if p.slice[3].type == 'PLUS':
				p[0].set_tzoff('+' + p.slice[4].value)
			else:
				p[0].set_tzoff('-' + p.slice[4].value)
		p[1] = None
		p[2] = None
		return 

	def p_day_format(self,p):
		''' day_format : NUMBER SLASH NUMBER SLASH NUMBER
		'''
		p[0] = dhcpconf.DayFormat(None,None,p.slice[1],p.slice[5])
		p[0].set_year(p.slice[1].value)
		p[0].set_month(p.slice[3].value)
		p[0].set_day(p.slice[5].value)
		return

	def p_time_format(self,p):
		''' time_format : NUMBER COLON NUMBER COLON NUMBER
		'''
		p[0] = dhcpconf.TimeFormat(None,None,p.slice[1],p.slice[5])
		p[0].set_hour(p.slice[1].value)
		p[0].set_minute(p.slice[3].value)
		p[0].set_second(p.slice[5].value)
		return

	def p_expr_op_basic(self,p):
		''' expr_op : basic_expr_op
		'''
		p[0] = p[1]
		p[1] = None
		return

	def p_expr_op_not_equal(self,p):
		''' expr_op : expr_op BANG EQUAL expr_op
		'''
		p[0] = dhcpconf.BangEqualExprOp(None,None,p[1],p[4])
		p[0].append_child(p[1])
		p[0].append_child(p[4])
		p[1] = None
		p[4] = None
		return

	def p_expr_op_equal(self,p):
		''' expr_op : expr_op EQUAL expr_op
		'''
		p[0] = dhcpconf.EqualExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_tidle_tidle(self,p):
		''' expr_op : expr_op TIDLE TIDLE expr_op
		'''
		p[0] = dhcpconf.IRegExpExprOp(None,None,p[1],p[4])
		p[0].append_child(p[1])
		p[0].append_child(p[4])
		p[1] = None
		p[4] = None
		return

	def p_expr_op_tidle_equal(self,p):
		''' expr_op : expr_op TIDLE EQUAL expr_op
		'''
		p[0] = dhcpconf.RegExpExprOp(None,None,p[1],p[4])
		p[0].append_child(p[1])
		p[0].append_child(p[4])
		p[1] = None
		p[4] = None
		return

	def p_expr_op_and(self,p):
		''' expr_op : expr_op AND expr_op
		'''
		p[0] = dhcpconf.AndExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_or(self,p):
		''' expr_op : expr_op AND expr_op
		'''
		p[0] = dhcpconf.OrExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_plus(self,p):
		''' expr_op : expr_op PLUS expr_op
		'''
		p[0] = dhcpconf.PlusExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_minus(self,p):
		''' expr_op : expr_op MINUS expr_op
		'''
		p[0] = dhcpconf.MinusExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_divide(self,p):
		''' expr_op : expr_op SLASH expr_op
		'''
		p[0] = dhcpconf.DivideExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_multiply(self,p):
		''' expr_op : expr_op ASTERISK expr_op
		'''
		p[0] = dhcpconf.MultiplyExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_mod(self,p):
		''' expr_op : expr_op PERCENT expr_op
		'''
		p[0] = dhcpconf.ModExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_bitand(self,p):
		''' expr_op : expr_op AMPERSAND expr_op
		'''
		p[0] = dhcpconf.BitAndExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_bitor(self,p):
		''' expr_op : expr_op PIPE expr_op
		'''
		p[0] = dhcpconf.BitOrExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return

	def p_expr_op_bitxor(self,p):
		''' expr_op : expr_op CARET expr_op
		'''
		p[0] = dhcpconf.BitXorExprOp(None,None,p[1],p[3])
		p[0].append_child(p[1])
		p[0].append_child(p[3])
		p[1] = None
		p[3] = None
		return


	def p_basic_expr_op(self,p):
		''' basic_expr_op : check_expr_op
		        | not_expr_op
		        | paren_expr_op
		        | exists_expr_op
		        | static_expr_op
		        | known_expr_op
		        | substring_expr_op
		        | suffix_expr_op
		        | lcase_expr_op
		        | ucase_expr_op
		        | concat_expr_op
		        | binary_to_ascii_expr_op
		        | reserve_expr_op
		        | pick_expr_op
		        | dns_update_expr_op
		        | dns_delete_expr_op
		        | ns_update_expr_op
		        | option_expr_op
		        | config_option_expr_op
		        | hardware_expr_op
		        | leased_address_expr_op
		        | client_state_expr_op
		        | filename_expr_op
		        | server_name_expr_op
		        | lease_time_expr_op
		        | null_expr_op
		        | host_decl_name_expr_op
		        | update_ddns_rr_expr_op
		        | packet_expr_op
		        | const_data_expr_op
		        | extract_int_expr_op
		        | encode_int_expr_op
		        | defined_expr_op
		        | gethostname_expr_op
		        | gethostbyname_expr_op
		        | user_define_func_expr_op
		'''
		p[0] = dhcpconf.NonBinaryExprOp()
		p[0].append_child(p[1])
		p[0].set_pos_by_children()
		p[1] = None
		return

	def p_data_expr_op(self,p):
		''' data_expr_op : expr_op
		'''
		p[0] = p[1]
		return

	def p_check_expr_op(self,p):
		''' check_expr_op : CHECK TEXT
		'''
		p[0] = dhcpconf.CheckExprOp(None,None,p.slice[1],p.slice[2])
		p[0].set_check_text(p.slice[2].value)
		return

	def p_not_expr_op(self,p):
		''' not_expr_op : NOT boolean_expr_op
		'''
		p[0] = dhcpconf.NotExprOp(None,None,p.slice[1],p[2])
		p[0].append_child(p[2])
		p[2] = None
		return

	def p_exists_expr_op(self,p):
		''' exists_expr_op : EXISTS option_name
		'''
		p[0] = dhcpconf.ExistsExprOp(None,None,p.slice[1],p[2])
		p[0].append_child(p[1])
		p[1] = None
		return

	def p_paren_expr_op(self,p):
		''' paren_expr_op : LPAREN expr_op RPAREN
		'''
		p[0] = dhcpconf.ParenExprOp(None,None,p.slice[1],p.slice[3])
		p[0].append_child(p[2])
		p[2] = None
		return

	def p_static_expr_op(self,p):
		''' static_expr_op : STATIC
		'''
		p[0] = dhcpconf.StaticExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_known_expr_op(self,p):
		''' known_expr_op : KNOWN
		'''
		p[0] = dhcpconf.KnownExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_substring_expr_op(self,p):
		''' substring_expr_op : SUBSTRING LPAREN data_expr_op COMMA NUMBER COMMA NUMBER RPAREN
		'''
		p[0] = dhcpconf.SubstringExprOp(None,None,p.slice[1],p.slice[8])
		p[0].set_parameter(p.slice[5].value,p.slice[7].value)
		return

	def p_suffix_expr_op(self,p):
		''' suffix_expr_op : SUFFIX LPAREN data_expr_op COMMA NUMBER RPAREN
		'''
		p[0] = dhcpconf.SuffixExprOp(None,None,p.slice[1],p.slice[6])
		p[0].append_child(p[3])
		p[0].set_parameter(p.slice[5].value)
		p[3] = None
		return

	def p_lcase_expr_op(self,p):
		''' lcase_expr_op : LCASE LPAREN data_expr_op RPAREN
		'''
		p[0] = dhcpconf.LcaseExprOp(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_ucase_expr_op(self,p):
		''' ucase_expr_op : UCASE LPAREN data_expr_op RPAREN
		'''
		p[0] = dhcpconf.UcaseExprOp(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_concat_expr_op(self,p):
		''' concat_expr_op : CONCAT LPAREN concat_param_list RPAREN
		'''
		p[0] = dhcpconf.ConcatExprOp(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_concat_param_list(self,p):
		''' concat_param_list : data_expr_op
		        | concat_param_list COMMA data_expr_op
		'''
		if len(p) == 2:
			p[0] = dhcpconf.ConcatParamList()
			p[0].append_child(p[1])
			p[0].set_pos_by_children()
			p[1] = None
		else:
			p[0] = p[1]
			p[0].append_child(p[3])
			p[0].set_pos_by_children()
			p[3] = None
			p[1] = None
		return

	def p_binary_to_ascii_expr_op(self,p):		
		''' binary_to_ascii_expr_op : BINARY_TO_ASCII LPAREN NUMBER COMMA NUMBER COMMA data_expr_op COMMA data_expr_op RPAREN
		'''
		## to base width seperator buffer
		p[0] = dhcpconf.BinaryToAsciiExprOp(None,None,p.slice[1],p.slice[10])
		p[0].set_base(p.slice[3].value)
		p[0].set_width(p.slice[5].value)
		p[0].set_seperator(p[7])
		p[0].set_buffer(p[9])
		p[7] = None
		p[9] = None
		return

	def p_reverse_expr_op(self,p):
		''' reverse_expr_op : REVERSE LPAREN NUMBER COMMA data_expr_op RPAREN
		'''
		p[0] = dhcpconf.ReverseExprOp(None,None,p.slice[1],p.slice[6])
		p[0].set_width(p.slice[3].value)
		p[0].set_buffer(p[5])
		p[5] = None
		return

	def p_pick_expr_op(self,p):
		''' pick_expr_op : PICK LPAREN pick_expr_op_param_list RPAREN
		'''
		p[0] = dhcpconf.PickExprOp(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_pick_expr_op_param_list(self,p):
		''' pick_expr_op_param_list : data_expr_op
				| pick_expr_op_param_list COMMA data_expr_op
		'''
		if len(p) == 2:
			p[0] = dhcpconf.PickExprOpParamList()
			p[0].append_child(p[1])
			p[0].set_pos_by_children()
			p[1] = None
		else:
			p[0] = p[1]
			p[0].append_child(p[3])
			p[0].set_pos_by_children()
			p[1] = None
			p[3] = None
		return

	def p_dns_update_expr_op(self,p):
		''' dns_update_expr_op : DNS_UPDATE LPAREN dns_type COMMA data_expr_op COMMA data_expr_op COMMA NUMBER RPAREN
		'''
		p[0] = dhcpconf.DnsUpdateExprOp(None,None,p.slice[1],p.slice[10])
		p[0].set_dns_type(p[3])
		p[0].set_dns_param1(p[5])
		p[0].set_dns_param2(p[7])
		p[0].set_dns_number(p.slice[9].value)
		p[3] = None
		p[5] = None
		p[7] = None
		return

	def p_dns_delete_expr_op(self,p):
		''' dns_delete_expr_op : DNS_DELETE LPAREN dns_type COMMA data_expr_op COMMA data_expr_op RPAREN
		'''
		p[0] = dhcpconf.DnsDeleteExprOp(None,None,p.slice[1],p.slice[8])
		p[0].set_dns_type(p[3])
		p[0].set_dns_param1(p[5])
		p[0].set_dns_param2(p[7])
		p[3] = None
		p[5] = None
		p[7] = None
		return

	def p_ns_update_expr_op(self,p):
		''' ns_update_expr_op : NS_UPDATE LPAREN ns_update_func_list RPAREN
		'''
		p[0] = dhcpconf.NsUpdateExprOp(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_ns_update_func_list(self,p):
		''' ns_update_func_list : ns_update_func
				| ns_update_func_list COMMA ns_update_func
		'''
		if len(p) == 2:
			p[0] = dhcpconf.NsUpdateFuncList(None,None)
			p[0].append_child(p[1])
			p[0].set_pos_by_children()
			p[1] = None
		else:
			p[0] = p[1]
			p[0].append_child(p[3])
			p[0].set_pos_by_children()
			p[1] = None
			p[3] = None
		return

	def p_ns_update_func(self,p):
		''' ns_update_func : dns_update_expr_op
				| dns_delete_expr_op
				| ns_add_expr_op
				| ns_delete_expr_op
				| ns_not_exists_expr_op
				| ns_exists_expr_op
		'''
		p[0] = dhcpconf.NsUpdateFunc()
		p[0].append_child(p[1])
		p[0].set_pos_by_children()
		p[1] = None
		return
	def p_ns_add_expr_op(self,p):
		''' ns_add_expr_op : ADD LPAREN ns_add_param_list RPAREN
		'''
		p[0] = dhcpconf.NsAddExprOp(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_ns_delete_expr_op(self,p):
		''' ns_delete_expr_op : DELETE LPAREN ns_param_list RPAREN
		'''
		p[0] = dhcpconf.NsDeleteExprOp(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_ns_exists_expr_op(self,p):
		''' ns_exists_expr_op : EXISTS LPAREN ns_param_list RPAREN
		'''
		p[0] = dhcpconf.NsExistsExprOp(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_ns_not_exists_expr_op(self,p):
		''' ns_not_exists_expr_op : NOT EXISTS LPAREN ns_param_list RPAREN
		'''
		p[0] = dhcpconf.NsNotExistsExprOp(None,None,p.slice[1],p.slice[4])
		p[0].append_child(p[3])
		p[3] = None
		return

	def p_ns_add_param_list(self,p):
		''' ns_add_param_list : ns_param_list COMMA NUMBER
		'''
		p[0] = p[1]
		p[0].set_dns_number(p.slice[3].value)
		p[0].set_endpos(p.slice[3])
		p[1] = None
		return

	def p_ns_param_list(self,p):
		''' ns_param_list : dns_class COMMA dns_type COMMA data_expr_op COMMA data_expr_op
		'''
		p[0] = dhcpconf.NsParamList(None,None,p[1],p[7])
		p[0].set_dns_class(p[1])
		p[0].set_dns_type(p[3])
		p[0].set_dns_param1(p[5])
		p[0].set_dns_param2(p[7])
		p[1] = None
		p[3] = None
		p[5] = None
		p[7] = None
		return

	def p_option_expr_op(self,p):
		''' option_expr_op : OPTION option_name
		'''
		p[0] = dhcpconf.OptionExprOp(None,None,p.slice[1],p[2])
		p[0].set_name(p[2])
		p[2] = None
		return

	def p_config_option_expr_op(self,p):
		''' config_option_expr_op : CONFIG_OPTION option_name
		'''
		p[0] = dhcpconf.ConfigOptionExprOp(None,None,p.slice[1],p[2])
		p[0].set_name(p[2])
		p[2] = None
		return

	def p_hardware_expr_op(self,p):
		''' hardware_expr_op : HARDWARE
		'''
		p[0] = dhcpconf.HardwareExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_leased_address_expr_op(self,p):
		''' leased_address_expr_op : LEASED_ADDRESS
		'''
		p[0] = dhcpconf.LeasedAddressExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_client_state_expr_op(self,p):
		''' client_state_expr_op : CLIENT_STATE
		'''
		p[0] = dhcpconf.ClientStateExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_filename_expr_op(self,p):
		''' filename_expr_op : FILENAME
		'''
		p[0] = dhcpconf.FilenameExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_server_name_expr_op(self,p):
		''' server_name_expr_op : SERVER_NAME
		'''
		p[0] = dhcpconf.ServerNameExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_lease_time_expr_op(self,p):
		''' lease_time_expr_op : LEASE_TIME
		'''
		p[0] = dhcpconf.LeaseTimeExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_null_expr_op(self,p):
		''' null_expr_op : NULL
		'''
		p[0] = dhcpconf.NullExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_host_decl_name_expr_op(self,p):
		''' host_decl_name_expr_op : HOST_DECL_NAME
		'''
		p[0] = dhcpconf.HostDeclNameExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_update_ddns_rr_expr_op(self,p):
		''' update_ddns_rr_expr_op : UPDATED_DNS_RR LPAREN ddns_type RPAREN
		'''
		p[0] = dhcpconf.UpdateDdnsRRExprOp(None,None,p.slice[1],p.slice[4])
		p[0].set_ddns_type(p[3])
		p[3] = None
		return

	def p_packet_expr_op(self,p):
		''' packet_expr_op : PACKET LPAREN NUMBER COMMA NUMBER RPAREN
		'''
		p[0] = dhcpconf.PacketExprOp(None,None,p.slice[1],p.slice[6])
		p[0].set_packet_pair(p.slice[3].value,p.slice[5].value)
		return

	def p_const_data_expr_op(self,p):
		''' const_data_expr_op : TEXT
		        | NUMBER
		        | FORMERR
		        | NOERROR
		        | NOTAUTH
		        | NOTIMP
		        | NOTZONE
		        | NXDOMAIN
		        | NXRRSET
		        | REFUSED
		        | SERVFAIL
		        | YXDOMAIN
		        | YXRRSET
		        | BOOTING
		        | REBOOT
		        | SELECT
		        | REQUEST
		        | BOUND
		        | RENEW
		        | REBIND
		'''
		p[0] = dhcpconf.ConstDataExprOp(None,None,p.slice[1],p.slice[1])
		p[0].set_const(p.slice[1].value)
		return

	def p_extract_int_expr_op(self,p):
		''' extract_int_expr_op : EXTRACT_INT LPAREN data_expr_op COMMA NUMBER RPAREN
		'''
		p[0] = dhcpconf.ExtractIntExprOp(None,None,p.slice[1],p.slice[6])
		p[0].set_target(p[3])
		p[0].set_offset(p.slice[5].value)
		p[3] = None
		return

	def p_encode_int_expr_op(self,p):
		''' encode_int_expr_op : ENCODE_INT LPAREN numeric_expr_op COMMA NUMBER RPAREN
		'''
		p[0] = dhcpconf.EncodeIntExprOp(None,None,p.slice[1],p.slice[6])
		p[0].set_target(p[3])
		p[0].set_offset(p.slice[5].value)
		return

	def p_formerr_expr_op(self,p):
		''' formerr_expr_op : FORMERR
		'''
		p[0] = dhcpconf.FormErrExprOp(None,None,p.slice[1],p.slice[1])
		return

	def p_defined_expr_op(self,p):
		''' defined_expr_op : DEFINED LPAREN  TEXT RPAREN
		'''
		p[0] = dhcpconf.DefinedExprOp(None,None,p.slice[1],p.slice[4])
		p[0].set_text(p.slice[3].value)
		return

	def p_gethostname_expr_op(self,p):
		''' gethostname_expr_op : GETHOSTNAME LPAREN RPAREN
		'''
		p[0] = dhcpconf.GetHostNameExprOp(None,None,p.slice[1],p.slice[3])
		return

	def p_gethostbyname_expr_op(self,p):
		''' gethostbyname_expr_op : GETHOSTBYNAME LPAREN TEXT RPAREN
		'''
		p[0] = dhcpconf.GetHostByNameExprOp(None,None,p.slice[1],p.slice[4])
		p[0].set_hostname(p.slice[3].value)
		return

	def p_user_define_func_expr_op(self,p):
		''' user_define_func_expr_op : TEXT LPAREN user_define_func_param_list RPAREN
		'''
		p[0] = dhcpconf.UserDefineFuncExprOp(None,None,p.slice[0],p.slice[4])
		p[0].set_funcname(p.slice[1].value)
		p[0].append_child(p[3])
		return

	def p_user_define_func_param_list_empty(self,p):
		''' user_define_func_param_list : empty
		'''
		p[0] = dhcpconf.UserDefineFuncParamList(None,None,p.slice[1],p.slice[1])
		p[1] = None
		return

	def p_user_define_func_param_list_recur(self,p):
		''' user_define_func_param_list : user_define_func_param_list COMMA expr_op
		'''
		p[0] = p[1]
		p[0].append_child(p[3])
		p[0].set_pos_by_children()
		p[1] = None
		return

	def p_user_define_func_param_list_expr_op(self,p):
		''' user_define_func_param_list : expr_op
		'''
		p[0] = dhcpconf.UserDefineFuncParamList()
		p[0].append_child(p[1])
		p[0].set_pos_by_children()
		return



	def p_ddns_type(self,p):
		''' ddns_type : TEXT
		'''
		p[0] = dhcpconf.DdnsType(None,None,p.slice[1],p.slice[1])
		p[0].set_type(p.slice[1].value)
		return

	def p_dns_type(self,p):
		'''dns_type : TEXT
				| NUMBER
		'''
		p[0] = dhcpconf.DnsType(None,None,p.slice[1],p.slice[1])
		if p.slice[1].type == 'TEXT':
			p[0].set_type(p.slice[1].value)
		else:
			p[0].set_inttype(p.slice[1].value)
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



