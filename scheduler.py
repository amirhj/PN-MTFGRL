import util, json, os, sys
from datetime import datetime


class Scheduler:
	def __init__(self, agents, fg, opt):
		self.agents = agents
		self.fg = fg
		self.opt = opt
		self.log = {}
		self.time = 0
		self.clock_log = []

	def init(self):
		for a in self.agents:
			self.log[a] = []

	def run(self):
		for a in self.agents:
			agent = self.agents[a]
			agent.start()

		test = 1
		for i in range(self.opt['episodes']+self.opt['tests']):
			self.time += 1
			if i < self.opt['episodes']:
				print "Episode", i+1, ":",
			else:
				print "Test", test, ":",
				if test == 1:
					for a in self.agents:
						agent = self.agents[a]
						agent.turn_off_learning()
				test += 1
			sys.stdout.flush()

			self.fg.reset()

			for a in self.agents:
				agent = self.agents[a]
				agent.reset()

			for a in self.agents:
				agent = self.agents[a]
				agent.ploy()

			termination = ''
			while True:
				if self.is_terminated():
					termination = 'Terminated'
					break

				if self.is_timeout():
					termination = 'Timeout'
					break

			for a in self.agents:
				agent = self.agents[a]
				agent.pauose()

			print termination

		# ***************************************
		#       Changing optimal point
		# ***************************************
		"""print "\n\nChange...\n\n"

		self.fg.func_calc.change()
		for a in self.agents:
			agent = self.agents[a]
			agent.turn_on_learning()

		test = 1
		for i in range(self.opt['episodes'] + self.opt['tests']):
			if i < self.opt['episodes']:
				print "Episode", i + 1, ":",
			else:
				print "Test", test, ":",
				if test == 1:
					for a in self.agents:
						agent = self.agents[a]
						agent.turn_off_learning()
				test += 1

			for a in self.agents:
				agent = self.agents[a]
				agent.reset()

			# self.fg.reset()

			termination = ''
			while True:
				if self.is_terminated():
					termination = 'Terminated'
					break

				if self.is_timeout():
					termination = 'Timeout'
					break

			print termination
		# ***************************************
		#     End of Changing optimal point
		# ***************************************
		"""
		for a in self.agents:
			agent = self.agents[a]
			agent.stoop()
			self.log[a] = agent.log

	def terminate(self):
		sys.stdout.flush()
		sys.stderr.flush()
		result = {'options': self.opt, 'result': {}}

		indices = util.Counter()
		variables = self.fg.vars.keys()

		for v in self.fg.vars:
			result['result'][str(v)] = self.fg.vars[v]['value']

		print 'Writing results...'
		folder = 'results/'+datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		os.mkdir(folder)
		os.mkdir(folder+'/qvalues')

		res = open(folder+'/result.txt', 'w')
		res.write(json.dumps(result, indent=4))
		res.close()

		res = open(folder+'/loog.txt', 'w')
		for line in self.agents['g1'].loog:
			res.write(line+'\n')
		res.close()

		res = open(folder+'/clock_log.txt', 'w')
		for i in range(len(self.clock_log)):
			res.write('%d %d\n' % (i+1, self.clock_log[i]))
		res.close()

		for a in self.log:
			i = 1
			name = a
			if isinstance(a, tuple):
				name = '-'.join(list(a))
			l = open(folder+'/'+name+'.txt', 'w')
			for r in self.log[a]:
				l.write("%d %d\n" % (i, r))
				i += 1
			l.close()

		for a in self.agents:
			i = 1
			agent = self.agents[a]
			name = a
			if isinstance(a, tuple):
				name = '-'.join(list(a))
			q = open(folder + '/qvalues/' + name + '.txt', 'w')
			for r in agent.qlog:
				q.write("%d %f\n" % (i, r))
				i += 1
			q.close()

		#"""
		print 'Getting solution by brute force...'
		max_sum = None
		max_vars = None
		while indices[variables[0]] < len(self.fg.vars[variables[0]]['domain']):
			dec = {}
			for v in variables:
				dec[v] = indices[v]
				self.fg.vars[v]['value'] = dec[v]

			totall_sum = 0
			for f in self.fg.funcs.keys():
				totall_sum += self.fg.get_value(f)

			if max_sum is None or max_sum < totall_sum:
				max_sum = totall_sum
				max_vars = dec

			for i in reversed(variables):
				if indices[i] < len(self.fg.vars[i]['domain']):
					indices[i] += 1
					if indices[i] == len(self.fg.vars[i]['domain']):
						if i != variables[0]:
							indices[i] = 0
					else:
						break

		result['optimal'] = max_vars
		#"""
		
		res = open(folder+'/result.txt', 'w')
		res.write(json.dumps(result, indent=4))
		res.close()

	def is_terminated(self):
		terminated = True
		max_clock = 0
		for a in self.agents:
			agent = self.agents[a]
			if not agent.is_terminated():
				terminated = False
				break
			else:
				if agent.clock > max_clock:
					max_clock = agent.clock

		if terminated:
			self.clock_log.append(max_clock)

		return terminated

	def is_timeout(self):
		timeout = False
		if self.opt['timeout'] > 0:
			for a in self.agents:
				agent = self.agents[a]
				if agent.clock >= self.opt['timeout']:
					timeout = True
					break
		if timeout:
			self.clock_log.append(self.opt['timeout'])

		return timeout
