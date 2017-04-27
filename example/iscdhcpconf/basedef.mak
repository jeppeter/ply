
ifndef __BASEDEF_MAK__
__BASEDEF_MAK__ := 1

PRINTF:=$(shell which printf)
OSNAME:=$(shell uname -s | tr [:upper:] [:lower:])
ECHO:=$(shell which echo)
MAKE:=$(shell which make)
PYTHON:=$(shell which python)
PERL:=$(shell which perl)
RM:=$(shell which rm)
BASH:=$(shell which bash)
DIFF:=$(shell which diff)
CHX:=$(shell which chmod) +x


define call_exec_echo
${PRINTF} "    %-9s %s\n" $(1) $(2);
endef

define call_run_command
$(1)
endef

ifeq (${Q},)
define call_exec_directly
$(call call_run_command,$(1))
endef
else
define call_exec_directly
$(call call_exec_echo,$(2),$(3)) $(call call_run_command,$(1))
endef
endif

define call_exec
${Q}$(call call_exec_directly,$(1),$(2),$(3))
endef

define readlink_f
$(shell ${PERL} -e "use strict;use Cwd \"abs_path\"; print abs_path(shift);" --  $(1) )
endef


## __BASEDEF_MAK__
endif 