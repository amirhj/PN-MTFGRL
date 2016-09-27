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
		self.name = name
		self.agents = agnets
		self.clock = 1
		self.log = []
		self.loog = []
		self.qlog = []
		self.episode_finished = True
		self.finished = False

		self.vars = None
		self.varlog = None
		self.varlock = threading.Lock()
		self.filelock = threading.Lock()

		self.qvalues = util.Counter()
		self.last_action = 'hold'
		self.infinity = float('-inf')

	def clone_vars(self):
		self.vars = self.fg.clone_vars()
		#print '\033[92m agent',self.name, ' cloned\033[0m'

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
		other_actions = [a for a in actions]

		max_q = None
		for a in actions:
			action_profile = self.get_actions_profile(a)
			q = (state,) + action_profile
			if (max_q is None) or (max_q < self.qvalues[q]):
				max_q = self.qvalues[q]
				max_action = a

		del other_actions[other_actions.index(max_action)]

		if util.flipCoin(self.epsilon):
			return random.choice(other_actions)
		return max_action

	def reward(self, state, action_profile, next_state):
		if self.is_terminated():
			r = 2.0
		else:
			action = action_profile[0]
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
				states = self.simulate(action)

			r = 0.1
			for a in states:
				s = states[a]
				diff = sum(s) - sum_state
				if diff > adiff:
					r = -0.1
					# print 'best is', a
					break
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
				states[a] = self.get_state()
		return states

	def update(self, state, action_profile, next_state, reward):
		qstate = (state, ) + action_profile
		sample = reward + self.opt['gamma'] * self.get_best_responce(next_state)
		leg = 'qstate from '+str(self.qvalues[qstate])
		self.qvalues[qstate] = (1 - self.alpha) * self.qvalues[qstate] + self.alpha * sample
		self.insert_log(leg+' to '+str(self.qvalues[qstate]))

	def is_terminated(self):
		actions = self.get_actions()
		state = self.get_state()
		terminate = True
		sum_state = sum(state)
		if sum_state == self.infinity:
			terminate = False
			self.insert_log('not terminated by -inf')
		else:
			if 'dec' in actions:
				if self.vars[self.name]['value'] > 0:
					self.dec()
					next_state = self.get_state()
					self.inc()
					diff = sum(next_state) - sum_state
					if diff > 0:
						terminate = False
						self.insert_log('not terminated by dec')
			if 'inc' in actions:
				if self.vars[self.name]['value'] < self.vars[self.name]['size'] - 1:
					self.inc()
					next_state = self.get_state()
					self.dec()
					diff = sum(next_state) - sum_state
					if diff > 0:
						terminate = False
						self.insert_log('not terminated by inc')
		if terminate:
			self.insert_log('terminated '+str(actions))
		return terminate

	def get_actions_profile(self, action):
		actions = [action]
		for a in self.fg.get_neighbour_variables(self.name):
			actions.append(self.agents[a].last_action)
		return tuple(actions)

	def run(self):
		while not self.finished:
			while (not self.episode_finished) and (self.clock < self.opt['timeout']):
				self.clone_vars()

				state = self.get_state()
				action = self.policy(state)
				v1 = self.vars[self.name]['value']
				self.commit(action)
				v2 = self.vars[self.name]['value']
				next_state = self.get_state()
				action_profile = self.get_actions_profile(action)
				reward = self.reward(state, action_profile, next_state)
				self.update(state, action_profile, next_state, reward)

				self.insert_log('in clock: '+str(self.clock))
				self.insert_log('in state: '+str(state)+' by '+str(v1))
				self.insert_log('takin action: '+str(action))
				self.insert_log('going to state: '+str(next_state)+' by '+str(v1))
				self.insert_log('with action profile: '+str(action_profile))
				self.insert_log('getting reward: '+str(reward))

				self.log.append(self.vars[self.name]['value'])
				self.qlog.append(sum(self.qvalues.values()))

				self.clock += 1

	def get_best_responce(self, state):
		agents = []
		action_indices = util.Counter()
		agents_actions = {}
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
		for c in cartesian:
			qstate = (state, ) + c
			if max_q is None or self.qvalues[qstate] > max_q:
				max_q = self.qvalues[qstate]

		return max_q

	def reset(self):
		self.clock = 1
		self.clone_vars()
		
		#self.filelock.acquire()
		#if self.varlog is not None:
		#	self.varlog.close()
		#self.varlog = open('log/%s.txt' % self.name, 'w')
		#self.filelock.release()

	def ploy(self):
		self.episode_finished = False

	def pauose(self):
		self.episode_finished = True
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
		self.varlock.acquire()
		v = self.vars[self.name]['value']
		if self.vars[self.name]['value'] < self.vars[self.name]['size'] -1:
			self.vars[self.name]['value'] += 1
			if self.vars[self.name]['value'] == self.vars[self.name]['size']:
				self.vars[self.name]['value'] = self.vars[self.name]['size'] -1
			#with self.filelock:
			#	self.varlog.write('inc %s from %d to %d\n' % (self.name, v, self.vars[self.name]['value']))
		self.varlock.release()

	def dec(self):
		self.varlock.acquire()
		v = self.vars[self.name]['value']
		if self.vars[self.name]['value'] > 0:
			self.vars[self.name]['value'] -= 1
			if self.vars[self.name]['value'] == -1:
				self.vars[self.name]['value'] = 0
			#with self.filelock:
			#	self.varlog.write('dec %s from %d to %d\n' % (self.name, v, self.vars[self.name]['value']))
		self.varlock.release()

