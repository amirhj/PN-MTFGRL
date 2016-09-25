import sys
from argparser import ArgParser
from factor_graph import FactorGraph
from functions import Functions2
from agent import Agent
from scheduler import Scheduler

print 'Reading options...'
opt_pattern = {'-e': {'name': 'episodes', 'type': 'int', 'default': 200},
               '--alpha': {'name': 'alpha', 'type': 'float', 'default': 0.9},
               '--gamma': {'name': 'gamma', 'type': 'float', 'default': 0.9},
               '--epsilon': {'name': 'epsilon', 'type': 'float', 'default': 0.2},
               '--temperature': {'name': 'temperature', 'type': 'float', 'default': 0.9},
               '-T': {'name': 'timeout', 'type': 'int', 'default': 200},
               '-t': {'name': 'tests', 'type': 'int', 'default': 20},
               '-a': {'name': 'auto_lines', 'type': 'bool', 'default': False},
               '-d': {'name': 'debug_level', 'type': 'int', 'default': 1}
               }
arg = ArgParser(sys.argv[2:], opt_pattern)
opt = arg.read()

for o in opt:
	print "\t", o, opt[o]
print

fg = FactorGraph(opt['auto_lines'])

fg.load(sys.argv[1])

print 'Factor graph loaded.'

agents = {}
for v in fg.vars:
	agents[v] = Agent(v, fg, opt, agents)


print "Number of relay nodes:", len(fg.nodes)
print "Number of power lines:", len(fg.powerLines)
print "Number of generators:", len(fg.generators)
print "Number of intermittent resources:", len(fg.resources)
print "Number of loads:", len(fg.loads)
print "\nNumber of variables:", len(fg.vars)
print "Number of functions:", len(fg.funcs)
print "\nNumber of agents:", len(agents)

sch = Scheduler(agents, fg, opt)
fg.scheduler = sch


"""
print "\nvariables:"
for v in fg.vars:
	print v,":"
	for f in fg.get_functions(v):
		print "\t",f
	for f in fg.get_neighbour_variables(v):
		print "\t**",f
print "\nfunctions:"
for f in fg.funcs:
	print f,":"
	for v in fg.funcs[f]['variables']:
		print "\t",v
print fg.powerLines
"""

sch.init()
sch.run()
sch.terminate()
#"""

