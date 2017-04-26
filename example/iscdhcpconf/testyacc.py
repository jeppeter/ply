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
        ''' statement :  option_statement
        '''
        children = []
        children.append(p[1])
        p[0] = dhcpconf.Statement(None,children,p[1],p[1])
        p[1] = None
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

