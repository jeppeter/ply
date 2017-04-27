ifeq (${V},)
Q=@
else
Q=
endif

include ./basedef.mak

CURDIR=.

all: test


test:testyacc.py testlex.py

testlex.py:testlex.py.tmpl
	$(call call_exec,${PYTHON} ${CURDIR}/makecode.py -i ${CURDIR}/keyword.json lclass -c ConfigDhcpLex $< $@,"GEN","$@")

testyacc.py:testyacc.py.tmpl
	$(call call_exec,${PYTHON} ${CURDIR}/makecode.py -i ${CURDIR}/keyword.json yclass -c ConfigDhcpYacc $< $@,"GEN","$@")


clean:
	$(call call_exec,${RM} -f testyacc.py testlex.py,"RM","test")
	$(call call_exec,${RM} -f parsetab.py,"RM","parsetab")