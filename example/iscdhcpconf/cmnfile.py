#! /usr/bin/env python


import sys
import logging
import subprocess

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

def write_file(s,outfile=None):
    fout = sys.stdout
    bmode = False
    if outfile is not None:
        fout = open(outfile,'wb')
    if 'b' in fout.mode:
        bmode = True

    if sys.version[0] == '2' or not bmode:
        fout.write('%s'%(s))
    else:
        fout.write(s.encode(encoding='UTF-8'))
    if fout != sys.stdout:
        fout.close()
    fout = None
    return

def expand_files(c):
	cmds = 'ls -a %s'%(c)
	p = subprocess.Popen('/bin/bash',shell=False,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
	retfiles = []
	boutmod = False
	binmod = False
	if 'b' in p.stdout.mode:
		boutmod = True
	if 'b' in p.stdin.mode:
		binmod = True
	if binmod and sys.version[0] != '2':
		cmds = cmds.encode(encoding='UTF-8')
	p.stdin.write(cmds)
	p.stdin.close()
	for l in p.stdout:
		if sys.version[0] != '2' and boutmod:
			l = l.decode(encoding='UTF-8')
		l = l.rstrip('\r\n')
		retfiles.append(l)
	p.stdout.close()
	p = None
	return retfiles
