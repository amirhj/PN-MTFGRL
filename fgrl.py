import sys
from argparser import ArgParser
from factor_graph import FactorGraph
from functions import Functions2
from agent import Agent
from scheduler import Scheduler

print 'Reading options...'
opt_pattern = {'-e': {'name': 'episodes', 'type': 'int', 'default': 200},
               '--alpha': {'name': 'alpha', 'type': 'float', 'default': 0.9},
               '--gamma': {'name': 'gamma', 'type': 'float', 'default': 0.8},
               '--epsilon': {'name': 'epsilon', 'type': 'float', 'default': 0.09},
               '--temperature': {'name': 'temperature', 'type': 'float', 'default': 0.9},
               '--landa': {'name': 'landa', 'type': 'int', 'default': 1},
               '-T': {'name': 'timeout', 'type': 'int', 'default': 200},
               '-t': {'name': 'tests', 'type': 'int', 'default': 20},
               '-a': {'name': 'auto_lines', 'type': 'bool', 'default': False},
               '-d': {'name': 'debug_level', 'type': 'int', 'default': 1},
               '-r': {'name': 'random_init', 'type': 'bool', 'default': False}
               }
arg = ArgParser(sys.argv[2:], opt_pattern)
opt = arg.read()

for o in opt:
	print "\t", o, opt[o]
print

fg = FactorGraph(opt)

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
print "\nNumber of agents:", len(agents), '\n'

sch = Scheduler(agents, fg, opt)
fg.scheduler = sch
"""
print '\t| '.join(['g0','t0','g1\t','v0','v1'])
print '-' * 50
v00
for g0 in range(fg.vars['g0']['size']):
	fg.vars['g0']['value'] = g0
	for t0 in range(fg.vars['t0']['size']):
		fg.vars['t0']['value'] = t0
		for g1 in range(fg.vars['g1']['size']):
			fg.vars['g1']['value'] = g1
			row = [str(fg.get_value('g0'))]
			row.append(str(fg.get_value('t0')))
			row.append(str(fg.get_value('g1'))+'\t')

			row.append(str(fg.get_value('v0')))
			row.append(str(fg.get_value('v1')))

			if g0 > 0:
				g0 -= 1
				fg.vars['g0']['value'] = g0

			print '\t| '.join(row)
sys.exit()

print '\t| '.join(['g1\t','v0'])
print '-' * 50

for g1 in range(fg.vars['g1']['size']):
	fg.vars['g1']['value'] = g1
	row = [str(fg.get_value('g1'))+'\t']

	row.append(str(fg.get_value('v0')))

	print '\t| '.join(row)
sys.exit()

for d in fg.vars['g1']['domain']:
	fg.vars['g1']['value'] = d
	agents['g1'].clone_vars()
	print '^^^', d, ', ',
	print fg.get_value('v0'), ', ',
	print fg.get_virtual_value('g1', agents['g1'].vars)
sys.exit()

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

