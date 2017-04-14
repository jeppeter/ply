# -----------------------------------------------------------------------------
# calc.py
#
# A simple calculator with variables.   This is from O'Reilly's
# "Lex and Yacc", p. 63.
#
# This example uses unicode strings for tokens, docstrings, and input.
# -----------------------------------------------------------------------------

import sys
sys.path.insert(0, "../..")
import ply.lex as lex

tokens = (
    'NAME', 'NUMBER',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'EQUALS',
    'LPAREN', 'RPAREN',
)

# Tokens

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_EQUALS = r'='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'

@lex.TOKEN(r'\d+')
def t_NUMBER(t):
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large", t.value)
        t.value = 0
    return t

t_ignore = u" \t"


@lex.TOKEN(r'\n+')
def t_newline(t):
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexfd = open('lexer.log','w')
lexlog = lex.PlyLogger(lexfd)
lexerobj = lex.lex(debug=True,optimize=True,debuglog=lexlog)

# Parsing rules
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
)

# dictionary of names
names = {}


def p_statement_assign(p):
    'statement : NAME EQUALS expression'
    names[p[1]] = p[3]


def p_statement_expr(p):
    'statement : expression'
    print(p[1])


def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    if p[2] == '+':
        p[0] = p[1] + p[3]
    elif p[2] == '-':
        p[0] = p[1] - p[3]
    elif p[2] == '*':
        p[0] = p[1] * p[3]
    elif p[2] == '/':
        p[0] = p[1] / p[3]


def p_expression_uminus(p):
    'expression : MINUS expression %prec UMINUS'
    p[0] = -p[2]


def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]


def p_expression_number(p):
    'expression : NUMBER'
    p[0] = p[1]


def p_expression_name(p):
    'expression : NAME'
    try:
        p[0] = names[p[1]]
    except LookupError:
        print("Undefined name '%s'" % p[1])
        p[0] = 0


def p_error(p):
    if p:
        print("Syntax error at '%s'" % p.value)
    else:
        print("Syntax error at EOF")

import ply.yacc as yacc
yaccfd = open('yacc.log','w')
yacclog = yacc.PlyLogger(yaccfd)
parser = yacc.yacc(debuglog=yacclog,debug=True,optimize=True)

while 1:
    try:
        if sys.version[0] == '2':
            s = raw_input('calc > ')
        else:
            s = input('calc > ')
    except EOFError:
        break
    if not s:
        continue    
    parser.parse(s,lexer=lexerobj,debug='parse.log')

if lexfd is not None:
    lexfd.close()
lexfd = None
if yaccfd is not None:
    yaccfd.close()
yaccfd = None