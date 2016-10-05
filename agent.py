import random
import util, sys
import threading


class Agent(threading.Thread):

	def __init__(self, name, fg, opt, agnets):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.fg = fg
		self.opt = opt
		self.alpha = opt['alpha']
		self.epsilon = opt['epsilon']
		self.landa = opt['landa']
		self.name = name
		self.agents = agnets
		self.clock = 1
		self.log = []
		self.loog = []
		self.qlog = []
		self.episode_finished = True
		self.finished = False
		self.terminated = False
		self.max_value = None
		self.max_solution = None
		self.q_queue = util.Queue()
		self.opt_cout = 0

		self.vars = None
		self.varlog = None
		self.varlock = threading.Lock()
		self.actions_profile = None

		self.qvalues = util.Counter()
		self.last_action = 'hold'
		self.infinity = float('-inf')

	def clone_vars(self):
		self.vars = self.fg.clone_vars()

	def get_actions(self):
		actions = ['dec', 'hold', 'inc']
		if self.vars[self.name]['value'] == 0:
			del actions[0]
		if self.vars[self.name]['value'] == self.vars[self.name]['size'] - 1:
			del actions[2]
		return actions

	def get_state(self):
		state = []
		for f in self.vars[self.name]['functions']:
			try:
				state.append(self.fg.get_virtual_value(f, self.vars))
			except Exception as e:
				print '\033[93m', self.vars, '\033[0m'
				print '\033[92mcalling by ',f, 'in ', self.name,'\033[0m'
				raise e
		return tuple(state)

	def policy(self, state):
		actions = self.get_actions()
		other_actions = set([a for a in actions])

		max_q = None
		max_actions = []
		for a in actions:
			q = (state,a) + self.actions_profile
			if (max_q is None) or (max_q < self.qvalues[q]):
				max_q = self.qvalues[q]
				max_actions = [a]
			elif max_q == self.qvalues[q]:
				max_actions.append(a)

		other_actions = list(other_actions - set(max_actions))

		if len(other_actions) > 0 and util.flipCoin(self.epsilon):
			return random.choice(other_actions)
		return random.choice(max_actions)

	def reward(self, state, action, next_state):
		if self.is_optimal():
			r = 2.0
		else:
			sum_state = sum(state)
			adiff = sum(next_state) - sum_state

			states = {}

			if action == 'inc':
				self.dec()
				states = self.simulate(action)
				self.inc()
			elif action == 'dec':
				self.inc()				
				states = self.simulate(action)
				self.dec()
			else:
				states = self.simulate(None)

			r = 0.1
			for a in states:
				s = states[a]
				diff = sum(s) - sum_state
				if diff > adiff:
					r = -3.0
					break
			self.insert_log('rewarding duo '+str(states))
		return r

	def commit(self, action):
		if action == 'inc':
			self.fg.inc(self.name)
			self.inc()
		elif action == 'dec':
			self.fg.dec(self.name)
			self.dec()

		self.last_action = action

	def simulate(self, action):
		actions = self.get_actions()
		states = {}
		for a in actions:
			if a != action:
				if a == 'inc':
					self.inc()
					states[a] = self.get_state()
					self.dec()
				elif a == 'dec':
					self.dec()
					states[a] = self.get_state()
					self.inc()
				else:
					states[a] = self.get_state()
		return states

	def updateo(self, state, action, next_state, reward):
		qstate = (state, action) + self.actions_profile
		sample = reward + self.opt['gamma'] * self.get_best_responce(next_state)
		leg = 'qstate ' + str(qstate) + ' from '+str(self.qvalues[qstate])
		self.qvalues[qstate] = (1 - self.alpha) * self.qvalues[qstate] + self.alpha * sample
		self.insert_log(leg+' to '+str(self.qvalues[qstate]))

	def is_optimal(self):
		actions = self.get_actions()
		state = self.get_state()
		terminate = True
		sum_state = sum(state)
		if sum_state == self.infinity:
			terminate = False
			self.insert_log('not optimal by -inf')
		else:
			if self.vars[self.name]['value'] > 0:
				self.dec()
				next_state = self.get_state()
				self.inc()
				if sum(next_state) > sum_state:
					terminate = False
					self.insert_log('not optimal by dec')
			if self.vars[self.name]['value'] < self.vars[self.name]['size'] - 1:
				self.inc()
				next_state = self.get_state()
				self.dec()
				if sum(next_state) > sum_state:
					terminate = False
					self.insert_log('not optimal by inc')

		if terminate:
			self.insert_log('optimal '+str(actions))

		return terminate

	def get_actions_profile(self):
		actions = []
		for a in self.fg.get_neighbour_variables(self.name):
			actions.append(self.agents[a].last_action)
		self.actions_profile = tuple(actions)

	def run(self):		

		self.varlog = open('log/%s.txt' % self.name, 'w')
		self.varlog.close()

		while not self.finished:
			while (not self.episode_finished) and (self.clock < self.opt['timeout']):
				self.clone_vars()
				self.get_actions_profile()

				state = self.get_state()
				action = self.policy(state)
				v1 = self.vars[self.name]['value']
				self.commit(action)
				v2 = self.vars[self.name]['value']
				next_state = self.get_state()
				self.log_state(next_state)

				self.insert_log('\nin clock: '+str(self.clock))
				self.insert_log('in state: '+str(state)+' by '+str(v1))
				self.insert_log('takin action: '+str(action))
				self.insert_log('going to state: '+str(next_state)+' by '+str(v2))
				self.insert_log('with action profile: '+str(self.actions_profile))


				reward = self.reward(state, action, next_state)

				self.insert_log('getting reward: '+str(reward))

				self.updateo(state, action, next_state, reward)

				self.log.append(self.vars[self.name]['value'])
				self.qlog.append(sum(self.qvalues.values()))

				self.clock += 1

	def get_best_responce(self, state):
		agents = [self.name]
		action_indices = util.Counter()
		agents_actions = {self.name: ['dec','hold','inc']}
		for a in self.fg.get_neighbour_variables(self.name):
			agents_actions[a] = self.agents[a].get_actions()
			agents.append(a)

		cartesian = []
		while action_indices[agents[0]] < len(agents_actions[agents[0]]):
			dec = []
			for v in agents:
				dec.append(agents_actions[v][action_indices[v]])
			cartesian.append(tuple(dec))

			for i in reversed(agents):
				if action_indices[i] < len(agents_actions[i]):
					action_indices[i] += 1
					if action_indices[i] == len(agents_actions[i]):
						if i != agents[0]:
							action_indices[i] = 0
					else:
						break

		max_q = None
		q = None
		for c in cartesian:
			qstate = (state, ) + c
			if max_q is None or self.qvalues[qstate] > max_q:
				max_q = self.qvalues[qstate]
				q = qstate
		self.insert_log(str(q) + ' = '+str(max_q) + ' is best responce')
		return max_q

	def reset(self):
		self.clock = 1
		self.terminated = False
		self.q_queue.flush()
		self.opt_cout = 0
		self.clone_vars()

	def ploy(self):
		self.episode_finished = False

	def pauose(self):
		self.episode_finished = True
		
		if self.max_solution is not None:
			self.varlog = open('log/%s.txt' % self.name, 'a')
			self.varlog.write('%d\n' % (self.max_solution))
			self.varlog.close()
		#print self.name, 'paused'

	def stoop(self):
		self.episode_finished = True
		self.finished = True

	def turn_off_learning(self):
		self.alpha = 0
		self.epsilon = 0

	def turn_on_learning(self):
		self.alpha = self.opt['alpha']
		self.epsilon = self.opt['epsilon']

	def insert_log(self, m):
		if self.name == 'g1':
			self.loog.append(m)

	def inc(self):
		v = self.vars[self.name]['value']
		if self.vars[self.name]['value'] < self.vars[self.name]['size'] -1:
			self.vars[self.name]['value'] += 1
			if self.vars[self.name]['value'] == self.vars[self.name]['size']:
				self.vars[self.name]['value'] = self.vars[self.name]['size'] -1

	def dec(self):
		v = self.vars[self.name]['value']
		if self.vars[self.name]['value'] > 0:
			self.vars[self.name]['value'] -= 1
			if self.vars[self.name]['value'] == -1:
				self.vars[self.name]['value'] = 0

	def log_state(self, state):
		"""sum_state = sum(state)
		if self.q_queue.size() == self.landa:
			self.q_queue.pop()
		self.q_queue.push(sum_state)

		if self.q_queue.size() == self.landa:
			if len(set(self.q_queue.list)) == 1:
				self.terminated = True
				self.episode_finished = True
		else:
			self.terminated = False

		if self.max_solution is not None:
			if self.max_value <= sum_state:
				#print self.max_value, 'is less than', sum_state
				self.max_value = sum_state
				self.max_solution = self.fg.get_virtual_value(self.name, self.vars)
		else:
			self.max_value = sum_state
			self.max_solution = self.fg.get_virtual_value(self.name, self.vars)"""
		optimal = self.is_optimal()
		if optimal:
			for a in self.fg.get_neighbour_variables(self.name):
				n_opt = True
				ov = sum([self.fg.get_virtual_value(f, self.vars) for f in self.vars[a]['functions']])
				if self.vars[a]['value'] < (self.vars[a]['size'] - 1):
					self.vars[a]['value'] += 1
					nv = sum([self.fg.get_virtual_value(f, self.vars) for f in self.vars[a]['functions']])
					self.vars[a]['value'] -= 1
					if ov > nv:
						n_opt = False
				if n_opt:
					if self.vars[a]['value'] > 0:
						self.vars[a]['value'] -= 1
						nv = sum([self.fg.get_virtual_value(f, self.vars) for f in self.vars[a]['functions']])
						self.vars[a]['value'] += 1
						if ov > nv:
							n_opt = False

				optimal = optimal and n_opt

				if not n_opt:
					break

			if optimal:
				self.opt_cout += 1
				if self.opt_cout == self.landa:
					self.max_solution = self.fg.get_virtual_value(self.name, self.vars)
					self.terminated = True
					self.episode_finished = True
			else:
				self.opt_cout = 0
				self.terminated = False
