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
             | hardware_statement
             | fixed_addr_statement
             | fixed_addr6_statement
             | pool_statement
             | range_statement
             | range6_statement
             | prefix6_statement
             | fixed_prefix6_statement
             | authoritative_statement
             | server_identifier_statement
             | option_statement
             | failover_statement
             | server_duid_statement
             | execute_statement
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
        ''' server_identifier_statement : SERVER_IDENTIFIER option_statement_part SEMI
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
        ''' option_name_value : OPTION option_name option_statement_part SEMI
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

    def p_option_statement_part_recur(self,p):
        ''' option_statement_part : option_tokens
        '''
        p[0] = dhcpconf.OptionStatementPart()
        p[0].append_child_and_set_pos(p[1])
        p[1] = None
        return

    def p_option_tokens(self,p):
        ''' option_tokens : empty
                | option_tokens option_token
        '''
        if len(p) == 2:
            p[0] = dhcpconf.OptionTokens(None,None,p[1],p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_option_token_simple(self,p):
        ''' option_token : TEXT
                | NUMBER
        '''
        consdata = dhcpconf.ConstDataExprOp(None,None,p.slice[1],p.slice[1])
        consdata.set_const(p.slice[1].value)
        p[0] = dhcpconf.OptionToken()
        p[0].append_child_and_set_pos(consdata)
        consdata = None
        return


    def p_option_token_compose(self,p):
        ''' option_token : domain_list                
        '''
        p[0] = dhcpconf.OptionToken()
        p[0].append_child_and_set_pos(p[1])
        p[1] = None
        return

    def p_domain_list(self,p):
        ''' domain_list : dns_name
                 | ipaddr
                 | domain_list COMMA dns_name
                 | domain_list COMMA ipaddr
        '''
        if len(p) == 2:
            p[0] = dhcpconf.DomainList()
            p[0].append_child_and_set_pos(p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_option_statement_part_code(self,p):
        ''' option_statement_part : CODE NUMBER EQUAL option_code_clauses
        '''
        p[0] = dhcpconf.OptionValue(None,None,p.slice[1],p[4])
        p[0].set_code_child(p.slice[2].value,p[4])
        p[4] = None
        return

    def p_option_statement_part_equal(self,p):
        ''' option_statement_part : EQUAL data_expression_op
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
    #   ''' host_name : host_name COLON TEXT
    #       | host_name COLON NUMBER
    #   '''     
    #   p[0] = p[1]
    #   p[0].append_colone_text(p.slice[3].value,p.slice[3])
    #   p[1] = None
    #   return

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
                 | NUMBER
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
        p[0].set_ipv6_pair(p[2],p[3])
        p[0].set_mask_number(p.slice[5].value)
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

    def p_fixed_addr_statement(self,p):
        ''' fixed_addr_statement : FIXED_ADDR fixed_addr_elements SEMI
        '''
        p[0] = dhcpconf.FixedAddrStatement(None,None,p.slice[1],p.slice[3])
        p[0].append_child(p[2])
        p[2] = None
        return

    def p_fixed_addr_elements(self,p):
        ''' fixed_addr_elements : host_name
                | fixed_addr_elements host_name
        '''
        if len(p) == 2:
            p[0] = dhcpconf.FixedAddrElements()
            p[0].append_child_and_set_pos(p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return



    def p_fixed_addr6_statement(self,p):
        ''' fixed_addr6_statement : FIXED_ADDR6 fixed_addr6_elements SEMI
        '''
        p[0] = dhcpconf.FixedAddr6Statement(None,None,p.slice[1],p.slice[3])
        p[0].append_child(p[2])
        p[2] = None
        return

    def p_fixed_addr6_elements(self,p):
        ''' fixed_addr6_elements : ipv6_addr
                | fixed_addr6_elements ipv6_addr
        '''
        if len(p) == 2:
            p[0] = dhcpconf.FixedAddr6Elements()
            p[0].append_child_and_set_pos(p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
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


    def p_pool_declarations_recursive(self,p):
        '''pool_declarations : empty
                | pool_declarations pool_declaration
        '''
        if len(p) == 2:
            p[0] = dhcpconf.PoolDeclarations(None,None,p[1],p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return


    def p_pool_declaration_no_failover(self,p):
        ''' pool_declaration : NO FAILOVER PEER SEMI
        '''
        p[0] = dhcpconf.Failover(None,None,p.slice[1],p.slice[4])
        return

    def p_pool_declaration_failover_peer(self,p):
        ''' pool_declaration : FAILOVER PEER dns_name SEMI
        '''
        p[0] = dhcpconf.Failover(None,None,p.slice[1],p.slice[4])
        p[0].append_child(p[3])
        p[3] = None
        return

    def p_pool_declaration_range_statement(self,p):
        '''pool_declaration : range_statement
                 | range6_statement
        '''
        p[0] = p[1]
        p[1] = None
        return

    def p_range_statement_pair(self,p):
        '''range_statement : RANGE ipv4_addr ipv4_addr SEMI
        '''
        p[0] = dhcpconf.RangeStatement(None,None,p.slice[1],p.slice[4])
        p[0].set_range_ips(p[2],p[3])
        p[2] = None
        p[3] = None
        return

    def p_range_statement_one(self,p):
        '''range_statement : RANGE ipv4_addr SEMI
        '''
        p[0] = dhcpconf.RangeStatement(None,None,p.slice[1],p.slice[3])
        p[0].set_range_ips(p[2],p[2])
        p[2] = None
        return


    def p_range_statement_part(self,p):
        '''range_statement : RANGE DYNAMIC_BOOTP ipv4_addr ipv4_addr SEMI
            | RANGE DYNAMIC_BOOTP ipv4_addr SEMI
        '''
        if len(p) == 5:
            p[0] = dhcpconf.RangeStatement(None,None,p.slice[1],p.slice[4])
            p[3] = None
        else:
            p[0] = dhcpconf.RangeStatement(None,None,p.slice[1],p.slice[5])
            p[3] = None
            p[4] = None
        p[0].set_dynamic()
        return

    def p_range6_statement_ipv6_slash(self,p):
        ''' range6_statement : RANGE6 ipv6_addr SLASH NUMBER SEMI
               | RANGE6 ipv6_addr SLASH NUMBER TEMPORARY SEMI
        '''
        p[0] = dhcpconf.Range6Statement(None,None,p.slice[1],p.slice[5])
        p[0].set_start_ip(p[2])
        p[0].set_mask_number(p.slice[4].value)
        p[2] = None
        if len(p) > 6:
            p[0].set_temporary()
        return

    def p_range6_statement_ipv6_two(self,p):
        ''' range6_statement : RANGE6 ipv6_addr ipv6_addr SEMI
        '''
        p[0] = dhcpconf.RangeStatement(None,None,p.slice[1],p.slice[4])
        p[0].set_ipv6_pair(p[2],p[3])
        p[2] = None
        p[3] = None
        return

    def p_range6_statement_ipv6_temp(self,p):
        ''' range6_statement : RANGE6 ipv6_addr TEMPORARY SEMI
                | RANGE6 ipv6_addr SEMI
        '''
        p[0] = dhcpconf.Range6Statement(None,None,p.slice[1],p.slice[4])
        p[0].set_start_ip(p[2])
        if len(p) > 4:
            p[0].set_temporary()
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

    def p_boolean_expr_op(self,p):
        ''' boolean_expr_op : expr_op
        '''
        p[0] = p[1]
        p[1] = None
        return

    def p_arg_list_empty(self,p):
        ''' arg_list : empty
        '''
        p[0] = dhcpconf.ArgList(None,None,p.slice[1],p.slice[1])
        p[1] = None
        return

    def p_arg_list_not_empty(self,p):
        ''' arg_list : arg_list_not_empty
        '''
        p[0] = p[1]
        p[1] = None
        return

    def p_arg_list_not_empty_recur(self,p):
        ''' arg_list_not_empty : expr_op
                  | arg_list_not_empty COMMA expr_op
        '''
        if len(p) == 2:
            p[0] = dhcpconf.ArgList()
            p[0].append_child_and_set_pos(p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[3])
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
                | func_call_expr_op
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


    def p_paren_expr_op(self,p):
        ''' paren_expr_op : LPAREN expr_op RPAREN
        '''
        p[0] = dhcpconf.ParenExprOp(None,None,p.slice[1],p.slice[3])
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

    def p_numeric_expr_op(self,p):
        ''' numeric_expr_op : expr_op
        '''
        p[0] = p[1]
        p[1] = None
        return

    def set_arg_list(self,p,clsname,paramok,fmts):
        clsfunc = self.get_class_init_name('dhcpconf.%s'%(clsname))
        if clsfunc is None:
            raise Exception('can not find [%s] class'%(clsname))
        p[0] = clsfunc(None,None,p.slice[1],p.slice[4])
        if isinstance(paramok,int):
            if len(p[3].children) != paramok:
                errstr = '[%s] not match %s parameter'%(p[3].location(),fmts)
                if paramok > 1:
                    errstr += 's'
                raise Exception(errstr)
        elif isinstance(paramok,list):
            if len(p[3].children) not in paramok:
                errstr = '[%s] not match %s parameters'%(p[3].location(),fmts)
                raise Exception(errstr)
        elif isinstance(paramok,str):
            spanexpr = re.compile('^(\d+)\-(\d+)$')
            plusexpr = re.compile('^(\d+)\+$')
            starexpr = re.compile('^(\d+)\*$')
            if spanexpr.match(paramok):
                m = spanexpr.findall(paramok)
                minnum = int(m[0])
                maxnum = int(m[1])
                if minnum > len(p[3].children) or maxnum < len(p[3].children):
                    errstr = '[%s] not match %s parameters'%(p[3].location(),fmts)
                    raise Exception(errstr)
            elif plusexpr.match(paramok):
                m = plusexpr.findall(paramok)
                minnum = int(m[0])
                if minnum >= len(p[3].children):
                    errstr = '[%s] not match %s parameters'%(p[3].location(),fmts)
                    raise Exception(errstr)
            elif starexpr.match(paramok):
                m = starexpr.findall(paramok)
                minnum = int(m[0])
                if minnum > len(p[3].children):
                    errstr = '[%s] not match %s parameters'%(p[3].location(),fmts)
                    raise Exception(errstr)
            else:
                errstr = 'not valid string [%s]'%(paramok)
                raise Exception(errstr)
        else:
            raise Exception('not supported paramok')
        p[0].extend_children(p[3].children)
        p[3] = None
        return


    def p_substring_expr_op(self,p):
        ''' substring_expr_op : SUBSTRING LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'SubstringExprOp',3,'substring(instr,offset,len)')
        return

    def p_suffix_expr_op(self,p):
        ''' suffix_expr_op : SUFFIX LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'SuffixExprOp',2,'suffix(instr,len)')
        return

    def p_lcase_expr_op(self,p):
        ''' lcase_expr_op : LCASE LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'LcaseExprOp',1,'lcase(instr)')
        return

    def p_ucase_expr_op(self,p):
        ''' ucase_expr_op : UCASE LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'UcaseExprOp',1,'ucase(instr)')
        return

    def p_concat_expr_op(self,p):
        ''' concat_expr_op : CONCAT LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'ConcatExprOp','1+','concat(basestr,instr,...)')
        return

    def p_binary_to_ascii_expr_op(self,p):      
        ''' binary_to_ascii_expr_op : BINARY_TO_ASCII LPAREN arg_list RPAREN
        '''
        ## to base width seperator buffer
        self.set_arg_list(p,'BinaryToAsciiExprOp',4,'binary-to-ascii(base,width,seperator,buffer)')
        return

    def p_reverse_expr_op(self,p):
        ''' reverse_expr_op : REVERSE LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'ReverseExprOp',2,'reverse(width,buffer)')
        return

    def p_pick_expr_op(self,p):
        ''' pick_expr_op : PICK LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'PickExprOp',r'1*','pick(a,...)')
        return

    def check_old_dns_type(self,arg1):
        valid_dns_type = ['a','aaaa','ptr','mx','cname','TXT']
        if arg1.value_format() not in valid_dns_type:
            errstr = '[%s] [%s] dnstype is not valid one must in %s'%(arg1.location(),arg1.value_format(),valid_dns_type)
            raise Exception(errstr)
        return


    def p_dns_update_expr_op(self,p):
        ## dns_update_expr_op : DNS_UPDATE LPAREN dns_type COMMA data_expr_op COMMA data_expr_op COMMA numeric_expr_op RPAREN
        ''' dns_update_expr_op : DSN_UPDATE LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'DnsUpdateExprOp',4,'dns_update(dnstype,arg1,arg2,arg3)')
        self.check_old_dns_type(p[0].children[0])
        return

    def p_dns_delete_expr_op(self,p):
        ## dns_delete_expr_op : DNS_DELETE LPAREN dns_type COMMA data_expr_op COMMA data_expr_op RPAREN
        ''' dns_delete_expr_op : DNS_DELETE LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'DnsDeleteExprOp',3,'dns_delete(dnstype,arg1,arg2)')
        self.check_old_dns_type(p[0].children[0])
        return

    def p_ns_update_expr_op(self,p):
        ''' ns_update_expr_op : NS_UPDATE LPAREN ns_update_func_list RPAREN
        '''
        p[0] = dhcpconf.NsUpdateExprOp(None,None,p.slice[1],p.slice[4])
        p[0].extend_children(p[3].children)
        p[3] = None
        return

    def p_ns_update_func_list(self,p):
        ''' ns_update_func_list : ns_update_func
                | ns_update_func_list COMMA ns_update_func
        '''
        if len(p) == 2:
            p[0] = dhcpconf.NsUpdateFuncList(None,None)
            p[0].append_child_and_set_pos(p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[3])
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
        p[0] = p[1]
        p[1] = None
        return

    def check_rrclass(self,arg1):
        v = arg1.value_format()
        valid_rrclass = ['in','chaos','hs']
        if v not in valid_rrclass:
            intexpr = re.compile('^[\d]+$')
            if not intexpr.match(v):
                errstr = '[%s] %s not valid rrclass %s'%(arg1.location(),v,valid_rrclass)
                raise Exception(errstr)
        return

    def check_rrtype(self,arg1):
        v = arg1.value_format()
        valid_rrtype = ['a','aaaa','ptr','mx','cname','TXT']
        if v not in valid_rrtype:
            intexpr =re.compile('^(\d+)$')
            if not intexpr.match(v):
                errstr = '[%s] [%s] not valid for rrtype %s'%(arg1.location(),v,valid_rrtype)
                raise Exception(errstr)
        return

    def p_ns_add_expr_op(self,p):
        ''' ns_add_expr_op : ADD LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'NsAddExprOp',5,'add(rrclass,rrtype,arg1,arg2,arg3)')
        self.check_rrclass(p[0].children[0])
        self.check_rrtype(p[0].children[1])
        return

    def p_ns_delete_expr_op(self,p):
        ''' ns_delete_expr_op : DELETE LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'NsDeleteExprOp',4,'delete(rrclass,rrtype,arg1,arg2)')
        self.check_rrclass(p[0].children[0])
        self.check_rrtype(p[0].children[1])
        return

    def p_ns_exists_expr_op(self,p):
        ''' ns_exists_expr_op : EXISTS LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'NsExistsExprOp',4,'exists(rrclass,rrtype,arg1,arg2)')
        self.check_rrclass(p[0].children[0])
        self.check_rrtype(p[0].children[1])
        return

    def p_ns_not_exists_expr_op(self,p):
        ''' ns_not_exists_expr_op : NOT EXISTS LPAREN ns_param_list RPAREN
        '''
        self.set_arg_list(p,'NsExistsExprOp',4,'not exists(rrclass,rrtype,arg1,arg2)')
        self.check_rrclass(p[0].children[0])
        self.check_rrtype(p[0].children[1])
        p[0].set_exists(False)
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

    def check_ddns_type(self,arg1):
        v = arg1.value_format()
        valid_ddns_type = ['a','ptr']
        if v not in valid_ddns_type:
            errstr = '[%s] %s not valid ddns type %s'%(arg1.location(),v,valid_ddns_type)
            raise Exception(errstr)
        return

    def p_update_ddns_rr_expr_op(self,p):
        ''' update_ddns_rr_expr_op : UPDATED_DNS_RR LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'UpdateDdnsRRExprOp',1,'update-dns-rr(ddnstype)')
        self.check_ddns_type(p[0].children[0])
        return

    def p_packet_expr_op(self,p):
        ''' packet_expr_op : PACKET LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'PacketExprOp',2,'packet(offset,len)')
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

    def check_const_int(self,arg1,paramok):
        if not issubclass(arg1.__class__,dhcpconf.ConstDataExprOp):
            errstr = '[%s] %s not valid Const data'%(arg1.location(),arg1.value_format())
            raise Exception()
        v = arg1.value_format()
        if isinstance(paramok,list) or isinstance(paramok,tuple):
            if v not in paramok:
                errstr = '[%s] %s not value in %s'%(arg1.location(),v,paramok)
                raise Exception(errstr)
        elif isinstance(paramok,str):
            if v != paramok:
                errstr = '[%s] %s not value %s'%(arg1.location(),v,paramok)
                raise Exception(errstr)
        else:
            errstr = '%s not valid paramok'%(paramok)
            raise Exception(errstr)
        return


    def p_extract_int_expr_op(self,p):
        ''' extract_int_expr_op : EXTRACT_INT LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'ExtractIntExprOp',2,'extract-int(buffer,size)')
        self.check_const_int(p[0].children[1],['8','16','32'])
        return

    def p_encode_int_expr_op(self,p):
        ''' encode_int_expr_op : ENCODE_INT LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'EncodeIntExprOp',2,'encode-int(number,mode)')
        self.check_const_int(p[0].children[1],['8','16','32'])
        return

    def p_formerr_expr_op(self,p):
        ''' formerr_expr_op : FORMERR
        '''
        p[0] = dhcpconf.FormErrExprOp(None,None,p.slice[1],p.slice[1])
        return

    def p_defined_expr_op(self,p):
        ''' defined_expr_op : DEFINED LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'DefinedExprOp',1,'defined(name)')
        return

    def p_gethostname_expr_op(self,p):
        ''' gethostname_expr_op : GETHOSTNAME LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'GetHostNameExprOp',0,'gethostname()')
        return

    def p_gethostbyname_expr_op(self,p):
        ''' gethostbyname_expr_op : GETHOSTBYNAME LPAREN arg_list RPAREN
        '''
        self.set_arg_list(p,'GetHostByNameExprOp',1,'gethostbyname(hostname)')
        return

    def p_func_call_expr_op(self,p):
        ''' func_call_expr_op : TEXT LPAREN arg_list RPAREN
        '''
        p[0] = dhcpconf.FuncCallExprOp(None,None,p.slice[0],p.slice[4])
        p[0].set_funcname(p.slice[1].value)
        p[0].expand_children(p[3].children)
        p[3] = None
        return


    def p_failover_statement_simple(self,p):
        '''failover_statement : FAILOVER PEER TEXT SEMI
        '''
        return

    def p_failover_statement_state_decl(self,p):
        ''' failover_statement : FAILOVER PEER TEXT STATE LBRACE failover_state_declarations RBRACE
        '''
        p[0] = dhcpconf.FailoverStatement(None,None,p.slice[1],p.slice[7])
        p[0].set_name(p.slice[3].value)
        p[0].append_child(p[6])
        p[0].set_statemode(True)
        p[6] = None
        return

    def p_failover_state_declarations(self,p):
        ''' failover_state_declarations : empty
                  | failover_state_declarations failover_state_declaration
        '''
        if len(p) == 2:
            p[0] = dhcpconf.FailoverStateDeclarations(None,None,p[1],p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_failover_state_declaration(self,p):
        ''' failover_state_declaration : failover_my_state
                 | failover_partner_state
                 | failover_mclt_state
        '''
        p[0] = dhcpconf.FailoverStateDeclaration()
        p[0].append_child_and_set_pos(p[1])
        p[1] = None
        return

    def p_failover_my_state(self,p):
        ''' failover_my_state : MY STATE failover_state_define SEMI
                 | MY STATE failover_state_define AT date_format SEMI
        '''
        if len(p) == 5:
            p[0] = dhcpconf.FailoverMyState(None,None,p[1],p.slice[4])
            p[0].set_state(p[3])
            p[3] = None
        elif len(p) == 7:
            p[0] = dhcpconf.FailoverMyState(None,None,p[1],p.slice[6])
            p[0].set_state(p[3])
            p[0].set_time(p[5])
            p[3] = None
            p[5] = None
        return

    def p_failover_partner_state(self,p):
        ''' failover_partner_state : PARTNER STATE failover_state_define SEMI
                 | PARTNER STATE failover_state_define AT date_format SEMI
        '''
        if len(p) == 5:
            p[0] = dhcpconf.FailoverPartnerState(None,None,p[1],p.slice[4])
            p[0].set_state(p[3])
            p[3] = None
        elif len(p) == 7:
            p[0] = dhcpconf.FailoverPartnerState(None,None,p[1],p.slice[6])
            p[0].set_state(p[3])
            p[0].set_time(p[5])
            p[3] = None
            p[5] = None
        return

    def p_failover_mclt_state(self,p):
        ''' failover_mclt_state : MCLT NUMBER SEMI
        '''
        p[0] = dhcpconf.FailoverMcltState(None,None,p.slice[1],p.slice[3])
        p[0].set_mclt(p.slice[2].value)
        return

    def p_failover_state_define(self,p):
        ''' failover_state_define : UNKNOWN_STATE
                  | PARTNER_DOWN
                  | NORMAL
                  | COMMUNICATIONS_INTERRUPTED
                  | CONFLICT_DONE
                  | RESOLUTION_INTERRUPTED
                  | POTENTIAL_CONFLICT
                  | RECOVER
                  | RECOVER_WAIT
                  | RECOVER_DONE
                  | SHUTDOWN
                  | PAUSED
                  | STARTUP
        '''
        p[0] = dhcpconf.FailoverStateDefine(None,None,p.slice[1],p.slice[1])
        p[0].set_state(p.slice[1].value)
        return


    def p_failover_statement_decl(self,p):
        ''' failover_statement : FAILOVER PEER TEXT LBRACE failover_declarations RBRACE
        '''
        p[0] = dhcpconf.FailoverStatement(None,None,p.slice[1],p.slice[6])
        p[0].set_name(p.slice[3].value)
        p[0].append_child(p[5])
        p[5] = None
        return

    def p_failover_declarations(self,p):
        ''' failover_declarations : empty
               | failover_declarations failover_declaration
        '''
        if len(p) == 2:
            p[0] = dhcpconf.FailoverDeclarations(None,None,p[1],p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_failover_declaration(self,p):
        ''' failover_declaration : failover_primary_declaration
                 | failover_secondary_declaration
                 | failover_address_declaration
                 | failover_port_declaration
                 | failover_max_lease_misbalance_declaration
                 | failover_max_lease_ownership_declaration
                 | failover_max_balance_declaration
                 | failover_min_balance_declaration
                 | failover_auto_partner_down_declaration
                 | failover_max_response_delay_declaration
                 | failover_max_unacked_updates_declaration
                 | failover_mclt_declaration
                 | failover_hba_declaration
                 | failover_split_declaration
                 | failover_load_declaration
        '''
        p[0] = dhcpconf.FailoverDeclaration()
        p[0].append_child_and_set_pos(p[1])
        p[1] = None
        return

    def p_failover_primary_declaration(self,p):
        ''' failover_primary_declaration : PRIMARY SEMI
        '''
        p[0] = dhcpconf.FailoverPrimarayDeclaration(None,None,p.slice[1],p.slice[2])
        return

    def p_failover_secondary_declaration(self,p):
        '''failover_secondary_declaration : SECONDARY SEMI
        '''
        p[0] = dhcpconf.FailoverSecondaryDeclaration(None,None,p.slice[1],p.slice[2])
        return

    def p_failover_address_declaration(self,p):
        ''' failover_address_declaration : failover_peer_selected ADDRESS dns_name SEMI
        '''
        p[0] = dhcpconf.FailoverAddressDeclaration(None,None,p[1],p.slice[4])
        p[0].set_dns_ip(p[3])
        p[0].set_peer_mode(p[1])
        p[3] = None
        p[1] = None
        return

    def p_failover_port_declaration(self,p):
        ''' failover_port_declaration : failover_peer_selected PORT NUMBER SEMI
        '''
        p[0] = dhcpconf.FailoverPortDeclaration(None,None,p[1],p.slice[4])
        p[0].set_port(p.slice[3].value)
        p[0].set_peer_mode(p[1])
        p[1] = None
        return
    def get_class_init_name(self,modname):
        modname = '__main__'
        clsname = n
        if '.'  in n:
            sarr = re.split('\.',n)
            modname = '.'.join(sarr[:-1])
            clsname = sarr[-1]  
        m = importlib.import_module(modname)
        clsname = getattr(m,clsname,None)
        if clsname is None:
            return None
        return clsname


    def failover_set_value_3(self,p,callname):
        clsfunc = self.get_class_init_name('dhcpconf.%s'%(callname))
        if clsfunc is None:
            raise Exception('can not find %s'%(callname))
        p[0] = clsfunc(None,None,p.slice[1],p.slice[3])
        p[0].set_value(p.slice[2].value)
        return

    def failover_set_value_4(self,p,callname):
        clsfunc = self.get_class_init_name('dhcpconf.%s'%(callname))
        if clsfunc is None:
            raise Exception('can not find %s'%(callname))
        p[0] = clsfunc(None,None,p[1],p.slice[4])
        p[0].set_value(p.slice[3].value)
        p[0].set_peer_mode(p[1])
        return


    def p_failover_max_lease_misbalance_declaration(self,p):
        ''' failover_max_lease_misbalance_declaration : MAX_LEASE_MISBALANCE NUMBER SEMI
        '''
        self.failover_set_value_3(p,'FailoverMaxLeaseMisbalanceDeclaration')
        return

    def p_failover_max_lease_ownership_declaration(self,p):
        ''' failover_max_lease_ownership_declaration : MAX_LEASE_OWNERSHIP NUMBER SEMI
        '''
        self.failover_set_value_3(p,'FailoverMaxLeaseOwnershipDeclaration')
        return

    def p_failover_max_balance_declaration(self,p):
        '''failover_max_balance_declaration : MAX_BALANCE NUMBER SEMI
        '''
        self.failover_set_value_3(p,'FailoverMaxBalanceDeclaration')
        return

    def p_failover_min_balance_declaration(self,p):
        '''failover_max_balance_declaration : MAX_BALANCE NUMBER SEMI
        '''
        self.failover_set_value_3(p,'FailoverMinBalanceDeclaration')
        return

    def p_failover_auto_partner_down_declaration(self,p):
        ''' failover_auto_partner_down_declaration : AUTO_PARTNER_DOWN NUMBER SEMI
        '''
        self.failover_set_value_3(p,'FailoverAuotPartnerDownDeclaration')
        return

    def p_failover_max_response_delay_declaration(self,p):
        ''' failover_max_response_delay_declaration : failover_peer_selected MAX_RESPONSE_DELAY NUMBER SEMI
        '''
        self.failover_set_value_4(p,'FailoverMaxResponseDelayDeclaration')
        return

    def p_failover_max_unacked_updates_declaration(self,p):
        ''' failover_max_unacked_updates_declaration : failover_peer_selected MAX_UNACKED_UPDATES NUMBER SEMI
        '''
        self.failover_set_value_4(p,'FailoverMaxUnackedUpdatesDeclaration')
        return

    def p_failover_mclt_declaration(self,p):
        ''' failover_mclt_declaration : MCLT NUMBER SEMI
        '''
        self.failover_set_value_3(p,'FailoverMcltDeclaration')
        return

    def p_failover_hba_declaration(self,p):
        ''' failover_hba_declaration : HBA hardware_addr SEMI
        '''
        p[0] = dhcpconf.FailoverHbaDeclaration(None,None,p.slice[1],p.slice[3])
        p[0].append_child(p[2])
        p[2] = None
        return

    def p_failover_split_declaration(self,p):
        ''' failover_split_declaration : SPLIT NUMBER SEMI
        '''
        self.failover_set_value_3(p,'FailoverSplitDeclaration')
        return

    def p_failover_load_declaration(self,p):
        ''' failover_load_declaration : LOAD BALANCE MAX SECONDS NUMBER SEMI
        '''
        p[0] = dhcpconf.FailoverLoadDeclaration(None,None,p.slice[1],p.slice[6])
        p[0].set_value(p.slice[5].value)
        return



    def p_failover_peer_selected_empty(self,p):
        ''' failover_peer_selected : empty
        '''
        p[0] = dhcpconf.FailoverPeerSelected(None,None,p[1],p[1])
        p[1] = None
        return

    def p_failover_peer_selected_peer(self,p):
        ''' failover_peer_selected : PEER
        '''
        p[0] = dhcpconf.FailoverPeerSelected(None,None,p.slice[1],p.slice[1])
        p[0].set_peer(True)
        return

    def p_server_duid_statement(self,p):
        ''' server_duid_statement : server_duid_en_declaration
               | server_duid_ll_declaration
               | server_duid_llt_declaration
               | server_duid_simple_declaration
        '''
        p[0] = dhcpconf.ServerDuidStatement()
        p[0].append_child_and_set_pos(p[1])
        p[1] = None
        return

    def p_server_duid_en_declaration(self,p):
        ''' server_duid_en_declaration : SERVER_DUID EN NUMBER TEXT SEMI
        '''
        p[0] = dhcpconf.ServerDuidEnDeclaration(None,None,p.slice[1],p.slice[5])
        p[0].set_number(p.slice[3].value)
        p[0].set_text(p.slice[4].value)
        return

    def p_server_duid_ll_declaration(self,p):
        ''' server_duid_ll_declaration : SERVER_DUID LL  SEMI
                 | SERVER_DUID LL hardware_type hardware_addr SEMI
        '''
        p[0] = dhcpconf.ServerDuidLLDeclaration(None,None,p.slice[1],p.slice[-1])
        if len(p) > 4:
            p[0].set_type(p[3])
            p[0].set_addr(p[4])
        return

    def p_server_duid_llt_declaration(self,p):
        ''' server_duid_llt_declaration : SERVER_DUID LLT SEMI
                | SERVER_DUID LL hardware_type NUMBER hardware_addr SEMI
        '''
        p[0] = dhcpconf.ServerDuidLLTDeclaration(None,None,p.slice[1],p.slice[-1])
        if len(p) > 4:
            p[0].set_type(p[3])
            p[0].set_time(p.slice[4].value)
            p[0].set_addr(p[5])
        return

    def p_server_duid_simple_declaration(self,p):
        ''' server_duid_simple_declaration : SERVER_DUID NUMBER TEXT SEMI
        '''
        p[0] = dhcpconf.ServerDuidSimpleDeclaration(None,None,p.slice[1],p.slice[-1])
        p[0].set_number(p.slice[2].value)
        p[0].set_text(p.slice[3].value)
        return

    def p_execuate_statements(self,p):
        ''' execute_statements : empty
              | execute_statements execute_statement
        '''
        if len(p) == 2:
            p[0] = dhcpconf.ExecuteStatements(None,None,p[1],p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_execute_statement(self,p):
        ''' execute_statement : db_time_format_exec
                | if_exec
                | add_exec
                | break_exec
                | send_exec
                | supersede_exec
                | option_exec
                | allow_exec
                | deny_exec
                | ignore_exec
                | default_exec
                | prepend_exec
                | append_exec
                | on_exec
                | switch_exec
                | case_exec
                | switch_default_exec
                | define_exec
                | set_exec
                | unset_exec
                | eval_exec
                | execuate_exec
                | return_exec
                | log_exec
                | zone_exec
                | key_exec
        '''
        p[0] = dhcpconf.ExecuteStatement()
        p[0].append_child_and_set_pos(p[1])
        p[1] = None
        return

    def p_db_time_format_exec(self,p):
        ''' db_time_format_exec : DB_TIME_FORMAT DEFAULT  SEMI
                | DB_TIME_FORMAT LOCAL SEMI
        '''
        p[0] = dhcpconf.DbTimeFormatExec(None,None,p.slice[1],p.slice[-1])
        p[0].set_type(p.slice[2].value)
        return

    def p_if_exec(self,p):
        ''' if_exec : IF if_exec_simple
                   | IF if_exec_simple ELSE brace_execute_statements
                   | IF if_exec_simple ELSIF elsif_exec_simple
        '''
        if len(p) == 3:
            p[0] = dhcpconf.IfExec(None,None,p.slice[1],p[2])
            p[0].append_if_condition(p[2])
            p[2] = None
        else:
            p[0] = dhcpconf.IfExec(None,None,p.slice[1],p[4])
            p[0].append_if_condition(p[2])
            if p.slice[3].value == 'else':
                p[0].append_else_execution(p[4])
            elif p.slice[3].value == 'elsif':
                p[0].extend_elsif_execution(p[4])
            p[2] = None
            p[4] = None
        return

    def p_if_exec_else_if(self,p):
        ''' if_exec : IF if_exec_simple ELSE IF elsif_exec_simple
        '''
        p[0] = dhcpconf.IfExec(None,None,p.slice[1],p[5])
        p[0].append_if_condition(p[2])
        p[0].extend_elsif_execution(p[5])
        return


    def p_if_exec_simple(self,p):
        ''' if_exec_simple : if_exec_boolean_expr_op brace_execute_statements
        '''
        p[0] = dhcpconf.IfExecSimple(None,None,p[1],p[2])
        p[0].set_condition(p[1])
        p[0].set_execution(p[2])
        p[1] = None
        p[2] = None
        return

    def p_if_exec_boolean_expr_op(self,p):
        ''' if_exec_boolean_expr_op : boolean_expr_op
                   | LPAREN if_exec_boolean_expr_op RPAREN
        '''
        if len(p) == 2:
            p[0] = p[1]
            p[1] = None
        else:
            p[0] = p[2]
            p[0].set_startpos(p.slice[1])
            p[0].set_endpos(p.slice[3])
            p[2] = None
        return

    def p_brace_execute_statements(self,p):
        ''' brace_execute_statements : LBRACE execute_statements RBRACE
        '''
        p[0] = p[3]
        p[0].set_startpos(p.slice[1])
        p[0].set_endpos(p.slice[3])
        p[3] = None
        return

    def p_elsif_exec_simple(self,p):
        ''' elsif_exec_simple : if_exec_simple
                  | if_exec_simple ELSIF elsif_exec_simple
                  | if_exec_simple ELSE brace_execute_statements
        '''
        if len(p) == 2:
            p[0] = dhcpconf.ElseIfExecSimple(None,None,p[1],p[1])
            p[0].append_if_condition(p[1])
            p[1] = None
        else:
            p[0] = dhcpconf.ElseIfExecSimple(None,None,p[1],p[3])
            p[0].append_if_condition(p[1])
            if p.slice[2] == 'else':
                p[0].append_else_execution(p[3])
            elif p.slice[2] == 'elsif':
                p[0].extend_elsif_execution(p[3])
            p[1] = None
            p[3] = None
        return

    def p_elsif_exec_simple_more(self,p):
        ''' elsif_exec_simple : if_exec_simple ELSE IF eseif_exec_simple
        '''
        p[0] = dhcpconf.ElseIfExecSimple(None,None,p[1],p[4])
        p[0].append_if_condition(p[1])
        p[0].extend_elsif_execution(p[4])
        return

    def p_add_exec(self,p):
        ''' add_exec : ADD TEXT SEMI
        '''
        p[0] = dhcpconf.AddExec(None,None,p.slice[1],p.slice[3])
        p[0].set_text(p.slice[2].value)
        return

    def p_bread_exec(self,p):
        ''' break_exec : BREAK SEMI
        '''
        p[0] = dhcpconf.BreakExec(None,None,p.slice[1],p.slice[2])
        return

    def set_option_name_exec_4(self,p,clsname):
        clsfunc = self.get_class_init_name('dhcpconf.%s'%(clsname))
        if clsfunc is None:
            raise Exception('can not find [%s]'%(clsname))
        p[0] = clsfunc(None,None,p.slice[1],p.slice[4])
        p[0].set_option_name(p[2])
        p[0].set_option_statement(p[3])
        p[2] = None
        p[3] = None
        return

    def p_send_exec(self,p):
        ''' send_exec : SEND option_name option_statement_part SEMI
        '''
        self.set_option_name_exec_4(p,'SendExec')
        return

    def p_supersed_exec(self,p):
        ''' supersed_exec : SUPERSEDE option_name option_statement_part SEMI
        '''
        self.set_option_name_exec_4(p,'SupersedeExec')
        return

    def p_option_exec(self,p):
        ''' option_exec : OPTION option_name option_statement_part SEMI
        '''
        self.set_option_name_exec_4(p,'OptionExec')
        return

    def p_allow_exec(self,p):
        ''' allow_exec : ALLOW permit_exec_flags SEMI
        '''
        p[0] = dhcpconf.AllowExec(None,None,p.slice[1],p.slice[3])
        p[0].set_flag(p[2])
        p[2] = None
        return

    def p_deny_exec(self,p):
        ''' deny_exec : DENY permit_exec_flags SEMI
        '''
        p[0] = dhcpconf.DenyExec(None,None,p.slice[1],p.slice[3])
        p[0].set_flag(p[2])
        p[2] = None
        return

    def p_ignore_exec(self,p):
        ''' ignore_exec : IGNORE permit_exec_flags SEMI
        '''
        p[0] = dhcpconf.IgnoreExec(None,None,p.slice[1],p.slice[3])
        p[0].set_flag(p[2])
        p[2] = None
        return

    def p_permit_exec_flags(self,p):
        ''' permit_exec_flags : BOOTP
                   | BOOTING
                   | DYNAMIC_BOOTP
                   | UNKNOWN_CLIENTS
                   | DUPLICATES
                   | DECLINES
                   | CLIENT_UPDATES
                   | LEASEQUERY
                   | IGNORE_CLIENT_UIDS
        '''
        p[0] = dhcpconf.PermitExecFlags(None,None,p.slice[1],p.slice[1])
        p[0].set_flag(p.slice[1].value)
        return

    def p_default_exec(self,p):
        ''' default_exec : DEFAULT option_name option_statements_part SEMI
        '''
        self.set_option_name_exec_4(p,'DefaultExec')
        return

    def p_prepend_exec(self,p):
        ''' prepend_exec : PREPEND option_name option_statements_part SEMI
        '''
        self.set_option_name_exec_4(p,'PrependExec')
        return

    def p_append_exec(self,p):
        ''' append_exec : APPEND  option_name option_statements_part SEMI
        '''
        self.set_option_name_exec_4(p,'AppendExec')
        return

    def p_on_exec(self,p):
        ''' on_exec : ON on_exec_states SEMI
                 |　ON on_exec_states LBRACE execute_statements RBRACE
        '''
        if len(p) == 4:
            p[0] = dhcpconf.OnExec(None,None,p.slice[1],p.slice[3])
            p[0].set_state(p[2])
            p[2] = None
        else:
            p[0] = dhcpconf.OnExec(None,None,p.slice[1],p.slice[5])
            p[0].set_state(p[2])
            p[0].append_child(p[4])
            p[2] = None
            p[4] = None
        return

    def p_on_exec_states(self,p):
        ''' on_exec_states : on_exec_state
                   | on_exec_states OR on_exec_state
        '''
        if len(p) == 2:
            p[0] = dhcpconf.OnExecStates()
            p[0].append_child_and_set_pos(p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_on_exec_state(self,p):
        ''' on_exec_state : EXPIRY
                 | COMMIT
                 | RELEASE
                 | TRANSMISSION
        '''
        p[0] = dhcpconf.OnExecState(None,None,p.slice[1],p.slice[1])
        p[0].set_state(p.slice[1].value)
        return

    def p_switch_exec_state(self,p):
        ''' switch_exec : SWITCH LPAREN expr_op RPAREN LBRACE execute_statements RBRACE
        '''
        p[0] = dhcpconf.SwitchExec(None,None,p.slice[1],p.slice[7])
        p[0].set_data_expr(p[3])
        p[0].append_child(p[6])
        p[3] = None
        p[6] = None
        return

    def p_case_exec_state(self,p):
        ''' case_exec : CASE expr_op COLON
        '''
        p[0] = dhcpconf.CaseExec(None,None,p.slice[1],p.slice[3])
        p[0].set_data_expr(p[2])
        p[2] = None
        return

    def p_switch_default_exec(self,p):
        ''' switch_default_exec : DEFAULT COLON
        '''
        p[0] = dhcpconf.SwitchDefaultExec(None,None,p.slice[1],p.slice[2])
        return

    def p_define_exec(self,p):
        ''' define_exec : DEFINE TEXT EQUAL expr_op SEMI
                  | DEFINE TEXT LPAREN arg_params RPAREN LBRACE execute_statements RBRACE
        '''
        if len(p) == 6:
            p[0] = dhcpconf.DefineExec(None,None,p.slice[1],p.slice[5])
            p[0].set_name(p.slice[2].value)
            p[0].set_expr_op(p[4])
            p[4] = None
        elif len(p) == 9:
            p[0] = dhcpconf.DefineExec(None,None,p.slice[1],p.slice[8])
            p[0].set_name(p.slice[2].value)
            p[0].set_args(p[4])
            p[0].append_child(p[7])
            p[4] = None
            p[7] = None
        else:
            raise Exception('can not parse in %d p'%(len(p)))
        return

    def p_set_exec(self,p):
        ''' set_exec : SET TEXT EQUAL expr_op SEMI
                  | SET TEXT LPAREN arg_params RPAREN LBRACE execute_statements RBRACE
        '''
        if len(p) == 6:
            p[0] = dhcpconf.SetExec(None,None,p.slice[1],p.slice[5])
            p[0].set_name(p.slice[2].value)
            p[0].set_expr_op(p[4])
            p[4] = None
        elif len(p) == 9:
            p[0] = dhcpconf.SetExec(None,None,p.slice[1],p.slice[8])
            p[0].set_name(p.slice[2].value)
            p[0].set_args(p[4])
            p[0].append_child(p[7])
            p[4] = None
            p[7] = None
        else:
            raise Exception('can not parse in %d p'%(len(p)))
        return

    def p_arg_params_empty(self,p):
        ''' arg_params : empty
        '''
        p[0] = dhcpconf.ArgParams(None,None,p[1],p[1])
        p[1] = None
        return
    def p_arg_params_list(self,p):
        ''' arg_params : arg_params_not_empty
        '''
        p[0] = p[1]
        return

    def p_args_params_not_empty(self,p):
        ''' arg_params_not_empty : TEXT
                  | arg_params_not_empty COMMA TEXT
        '''
        if len(p) == 2:
            p[0] = dhcpconf.ArgParams(None,None,p.slice[1],p.slice[1])
            p[0].append_param(p.slice[1].value)
        elif len(p) == 4:
            p[0] = p[1]
            p[0].append_param(p.slice[3].value)
            p[0].set_endpos(p.slice[3])
            p[1] = None
        else:
            raise Exception('can not parse in %d p'%(len(p)))
        return

    def p_unset_exec(self,p):
        ''' unset_exec : UNSET TEXT SEMI
        '''
        p[0] = dhcpconf.UnsetExec(None,None,p.slice[1],p.slice[3])
        p[0].set_name(p.slice[2].value)
        return

    def p_eval_exec(self,p):
        ''' eval_exec : EVAL expr_op SEMI
        '''
        p[0] = dhcpconf.EvalExec(None,None,p.slice[1],p.slice[3])
        p[0].append_child(p[2])
        p[2] = None
        return

    def p_execute_exec(self,p):
        ''' execute_exec : EXECUTE LPAREN TEXT execute_exec_exprs BPAREN SEMI
        '''
        p[0] = dhcpconf.ExecuteExec(None,None,p.slice[1],p.slice[5])
        p[0].set_name(p.slice[3].value)
        p[0].append_child(p[4])
        p[4] = None
        return

    def p_execute_exec_exprs(self,p):
        ''' execute_exec_exprs : empty
                  | execute_exec_exprs COMMA data_expr_op
        '''
        if len(p) == 2:
            p[0] = dhcpconf.ExecuteExecExprs(None,None,p[1],p[1])
            p[1] = None
        elif len(p) == 4:
            p[0] = p[1].append_child_and_set_pos(p[3])
            p[1] = None
            p[3] = None
        else:
            raise Exception('can not parse in %d p'%(len(p)))
        return

    def p_return_exec(self,p):
        ''' return_exec : RETURN expr_op SEMI
        '''
        p[0] = dhcpconf.ReturnExec(None,None,p.slice[1],p.slice[3])
        p[0].append_child(p[2])
        p[2] = None
        return

    def p_log_exec(self,p):
        ''' log_exec : LOG LPAREN log_exec_level data_expr_op RPAREN SEMI
        '''
        p[0] = dhcpconf.LogExec(None,None,p.slice[1],p.slice[6])
        p[0].set_level(p[3])
        p[0].append_child(p[4])
        p[3] = None
        p[4] = None
        return

    def p_log_exec_level(self,p):
        ''' log_exec_level : empty
                | FATAL COMMA
                | ERROR COMMA
                | DEBUG COMMA
                | INFO COMMA
        '''
        if len(p) == 2:
            p[0] = dhcpconf.LogExecLevel(None,None,p[1],p[1])
            p[1] = None
        elif len(p) == 3:
            p[0] = dhcpconf.LogExecLevel(None,None,p.slice[1],p.slice[2])
            p[0].set_level(p.slice[1].value)
        else:
            raise Exception('can not parse in %d p'%(len(p)))
        return

    def p_zone_exec(self,p):
        ''' zone_exec : ZONE host_name LBRACE zone_exec_delcarations RBRACE
        '''
        p[0] = dhcpconf.ZoneExec(None,None,p.slice[1],p.slice[5])
        p[0].set_host(p[2])
        p[0].append_child(p[4])
        p[2] = None
        p[4] = None
        return

    def p_zone_exec_declarations(self,p):
        ''' zone_exec_declarations : empty
                | zone_exec_declarations zone_exec_declaration
        '''
        if len(p) == 2:
            p[0] = dhcpconf.ZoneExecDeclarations(None,None,p[1],p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_zone_exec_declaration(self,p):
        ''' zone_exec_declaration : zone_exec_primary_declaration
                  | zone_exec_secondary_declaration
                  | zone_exec_primary6_declaration
                  | zone_exec_secondary6_declaration
                  | zone_exec_key_declaration
        '''
        p[0] = dhcpconf.ZoneExecDeclaration()
        p[0].append_child_and_set_pos(p[1])
        p[1] = None
        return

    def set_zone_declaration_3(self,p,clsname):
        clsfunc = self.get_class_init_name('dhcpconf.%s'%(clsname))
        if clsfunc is None:
            raise Exception('can not get [%s]'%(clsname))
        p[0] = clsfunc(None,None,p.slice[1],p.slice[3])
        p[0].append_child(p[2])
        p[2] = None
        return

    def p_zone_exec_primary_declaration(self,p):
        ''' zone_exec_primary_declaration : PRIMARY host_name_list SEMI
        '''
        self.set_zone_declaration_3(p,'ZoneExecPrimaryDeclaration')
        return

    def p_zone_exec_secondary_declaration(self,p):
        ''' zone_exec_secondary_declaration : SECONDARY host_name_list SEMI
        '''
        self.set_zone_declaration_3(p,'ZoneExecSecondaryDeclaration')
        return

    def p_zone_exec_primary6_declaration(self,p):
        ''' zone_exec_primary6_declaration : PRIMARY6 ipv6_addr_list SEMI
        '''
        self.set_zone_declaration_3(p,'ZoneExecPrimary6Declaration')
        return

    def p_zone_exec_secondary6_declaration(self,p):
        ''' zone_exec_secondary6_declaration : SECONDARY6 ipv6_addr_list SEMI
        '''
        self.set_zone_declaration_3(p,'ZoneExecSecondary6Declaration')
        return

    def p_zone_exec_key_declaration(self,p):
        ''' zone_exec_key_declaration : KEY host_name SEMI
        '''
        self.set_zone_declaration_3(p,'ZoneExecKeyDeclaration')
        return


    def p_host_name_list(self,p):
        ''' host_name_list : host_name
              | host_name_list COMMA host_name
        '''
        if len(p) == 2:
            p[0] = dhcpconf.HostNameList()
            p[0].append_child_and_set_pos(p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_ipv6_addr_list(self,p):
        ''' ipv6_addr_list : ipv6_addr
               | ipv6_addr_list COMMA ipv6_addr
        '''
        if len(p) == 2:
            p[0] = dhcpconf.Ipv6AddrList()
            p[0].append_child_and_set_pos(p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_key_exec(self,p):
        ''' key_exec : KEY host_name LBRACE key_exec_declarations RBRACE
                  | KEY host_name LBRACE key_exec_declarations RBRACE SEMI
        '''
        p[0] = dhcpconf.KeyExec(None,None,p.slice[1],p.slice[-1])
        p[0].set_name(p[2])
        p[0].append_child(p[4])
        p[2] = None
        p[4] = None
        return

    def p_key_exec_declarations(self,p):
        ''' key_exec_declarations : empty
                 | key_exec_declarations key_exec_declaration
        '''
        if len(p) == 0:
            p[0] = dhcpconf.KeyExecDeclarations(None,None,p[1],p[1])
            p[1] = None
        else:
            p[0] = p[1].append_child_and_set_pos(p[2])
            p[1] = None
            p[2] = None
        return

    def p_key_exec_declaration(self,p):
        ''' key_exec_declaration : key_exec_algorithm_declaration
               | key_exec_secret_declaration
        '''
        p[0] = dhcpconf.KeyExecDeclaration()
        p[0].append_child_and_set_pos(p[1])
        p[1] = None
        return

    def p_key_exec_algorithm_declaration(self,p):
        ''' key_exec_algorithm_declaration : ALGORITHM host_name  SEMI
        '''
        p[0] = dhcpconf.KeyExecAlgorithmDeclaration(None,None,p.slice[1],p.slice[3])
        p[0].append_child(p[2])
        p[2] = None
        return

    def p_key_exec_secret_declaration(self,p):
        ''' key_exec_secret_declaration : KEY base64_text SEMI
        '''
        p[0] = dhcpconf.KeyExecKeyDeclaration(None,None,p.slice[1],p.slice[3])
        p[0].append_child(p[2])
        p[2] = None
        return

    def p_base64_text(self,p):
        ''' base64_text : empty
             | base64_text TEXT
             | base64_text NUMBER
             | base64_text EQUAL
             | base64_text PLUS
             | base64_text SLASH
        '''
        if len(p) == 2:
            p[0] = dhcpconf.Base64Text(None,None,p[1],p[1])
            p[1] = None
        elif len(p) == 3:
            p[0] = p[1]
            p[0].append_text(p.slice[2].value)
            p[1] = None
        else:
            raise Exception('can not parse in %d p'%(len(p)))
        return



    def p_empty(self,p):
        ''' empty :     
        '''
        startpos = dhcpconf.Location(p.lexer.lineno,(p.lexer.lexpos-p.lexer.linepos),p.lexer.lineno,(p.lexer.lexpos-p.lexer.linepos))
        p[0] = dhcpconf.YaccDhcpObject('Empty',None,startpos,startpos)
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



