ifeq (${V},)
Q=@
else
Q=
endif

include ./basedef.mak

CURDIR=.

all: test


test:testyacc.py testlex.py tgtlex.py tgtyacc.py

testlex.py:testlex.py.tmpl iscconf.json
	$(call call_exec,${PYTHON} ${CURDIR}/makecode.py -i ${CURDIR}/iscconf.json lclass -c ConfigDhcpLex $< $@,"GEN","$@")

testyacc.py:testyacc.py.tmpl iscconf.json
	$(call call_exec,${PYTHON} ${CURDIR}/makecode.py -i ${CURDIR}/iscconf.json yclass -c ConfigDhcpYacc $< $@,"GEN","$@")

tgtlex.py:tgtlex.py.tmpl tgtconf.json
	$(call call_exec,${PYTHON} ${CURDIR}/makecode.py -i ${CURDIR}/tgtconf.json lclass -c TgtConfigLex $< $@,"GEN","$@")

tgtyacc.py:tgtyacc.py.tmpl tgtconf.json
	$(call call_exec,${PYTHON} ${CURDIR}/makecode.py -i ${CURDIR}/tgtconf.json yclass -c TgtConfigYacc $< $@,"GEN","$@")

clean:
	$(call call_exec,${RM} -f testyacc.py testlex.py *.pyc,"RM","test")
	$(call call_exec,${RM} -f parsetab.py,"RM","parsetab")
	$(call call_exec,${RM} -f codeparse.py clauseparse.py testparse.py pyclause.py pycode.py,"RM","parse python")
	$(call call_exec,${RM} -f tgtlex.py tgtyacc.py,"RM","tgt")
	$(call call_exec,${RM} -rf ${CURDIR}/__pycache__,"RM","__pycache__")
