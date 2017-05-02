ifeq (${V},)
Q=@
else
Q=
endif

include ./basedef.mak

CURDIR=.

all: test


test:testyacc.py testlex.py

testlex.py:testlex.py.tmpl keyword.json
	$(call call_exec,${PYTHON} ${CURDIR}/makecode.py -i ${CURDIR}/keyword.json lclass -c ConfigDhcpLex $< $@,"GEN","$@")

testyacc.py:testyacc.py.tmpl keyword.json
	$(call call_exec,${PYTHON} ${CURDIR}/makecode.py -i ${CURDIR}/keyword.json yclass -c ConfigDhcpYacc $< $@,"GEN","$@")


clean:
	$(call call_exec,${RM} -f testyacc.py testlex.py *.pyc,"RM","test")
	$(call call_exec,${RM} -f parsetab.py,"RM","parsetab")
	$(call call_exec,${RM} -f codeparse.py clauseparse.py testparse.py pyclause.py pycode.py,"RM","parse python")
	$(call call_exec,${RM} -rf ${CURDIR}/__pycache__,"RM","__pycache__")
