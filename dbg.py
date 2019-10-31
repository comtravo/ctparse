import ctparse
import pprint
pprint.pprint(list(ctparse.ctparse_gen("at 7.6 evening/night",  max_stack_depth=0, timeout=0)))
