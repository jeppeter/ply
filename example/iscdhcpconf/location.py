#! /usr/bin/env python

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
