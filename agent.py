import random
import util
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
		self.qlog = []
		self.episode_finished = True
		self.finished = False

		self.qvalues = util.Counter()
		self.last_action = 'hold'

	def get_actions(self):
		actions = ['dec', 'hold', 'inc']
		if self.fg.vars[self.name]['value'] == 0:
			del actions[0]
		if self.fg.vars[self.name]['value'] == self.fg.vars[self.name]['size'] - 1:
			del actions[2]
		return actions

	def get_state(self):
		state = []
		for f in self.fg.vars[self.name]['functions']:
			state.append(self.fg.get_value(f))
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
			adiff = sum(next_state) - sum(state)
			actions = self.get_actions()

			if action == 'inc':
				if self.fg.vars[self.name]['value'] < self.fg.vars[self.name]['size'] - 1:
					self.fg.vars[self.name]['value'] -= 1
					actions = self.get_actions()
					self.fg.vars[self.name]['value'] += 1
					if 'inc' in actions:
						del actions[actions.index('inc')]
			elif action == 'dec':
				if self.fg.vars[self.name]['value'] > 0:
					self.fg.vars[self.name]['value'] += 1
					actions = self.get_actions()
					self.fg.vars[self.name]['value'] -= 1
					if 'dec' in actions:
						del actions[actions.index('dec')]
			else:
				actions = self.get_actions()
				if 'hold' in actions:
					del actions[actions.index('hold')]

			r = 0.1
			for a in actions:
				s = self.simulate(a)
				diff = sum(s) - sum(state)
				if diff > adiff:
					r = -0.1
					# print 'best is', a
					break
		return r

	def commit(self, action):
		if action == 'inc':
			if self.fg.vars[self.name]['value'] < self.fg.vars[self.name]['size']-1:
				self.fg.vars[self.name]['value'] += 1
		elif action == 'dec':
			if self.fg.vars[self.name]['value'] > 0:
				self.fg.vars[self.name]['value'] -= 1

		self.last_action = action

	def simulate(self, action):
		state = self.get_state()
		if action == 'inc':
			if self.fg.vars[self.name]['value'] < self.fg.vars[self.name]['size'] - 1:
				self.fg.vars[self.name]['value'] += 1
				state = self.get_state()
				self.fg.vars[self.name]['value'] -= 1

		elif action == 'dec':
			if self.fg.vars[self.name]['value'] > 0:
				self.fg.vars[self.name]['value'] -= 1
				state = self.get_state()
				self.fg.vars[self.name]['value'] += 1
		return state

	def update(self, state, action_profile, next_state, reward):
		qstate = (state, ) + action_profile
		sample = reward + self.opt['gamma'] * self.get_best_responce(next_state)
		self.qvalues[qstate] = (1 - self.alpha) * self.qvalues[qstate] + self.alpha * sample

	def is_terminated(self):
		actions = self.get_actions()
		state = self.get_state()
		terminate = True
		if 'dec' in actions:
			if self.fg.vars[self.name]['value'] > 0:
				self.fg.vars[self.name]['value'] -= 1
				next_state = self.get_state()
				self.fg.vars[self.name]['value'] += 1
				diff = sum(next_state) - sum(state)
				if diff > 0:
					terminate = False
		if 'inc' in actions:
			if self.fg.vars[self.name]['value'] < self.fg.vars[self.name]['size'] - 1:
				self.fg.vars[self.name]['value'] += 1
				next_state = self.get_state()
				self.fg.vars[self.name]['value'] -= 1
				diff = sum(next_state) - sum(state)
				if diff > 0:
					terminate = False
		return terminate

	def get_actions_profile(self, action):
		actions = [action]
		for a in self.fg.get_neighbour_variables(self.name):
			actions.append(self.agents[a].last_action)
		return tuple(actions)

	def run(self):
		while not self.finished:
			# print 'just hanging here', self.episode_finished, self.clock, self.opt['timeout']
			while (not self.episode_finished) and (self.clock < self.opt['timeout']):
				# if self.name == 'x1':
				# 	print 'in x1'
				state = self.get_state()
				action = self.policy(state)
				self.commit(action)
				next_state = self.get_state()
				action_profile = self.get_actions_profile(action)
				reward = self.reward(state, action_profile, next_state)
				self.update(state, action_profile, next_state, reward)

				self.log.append(self.fg.vars[self.name]['value'])
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
		self.episode_finished = False
		self.clock = 1

	def stop(self):
		self.episode_finished = False
		self.finished = True

	def turn_off_learning(self):
		self.alpha = 0
		self.epsilon = 0

	def turn_on_learning(self):
		self.alpha = self.opt['alpha']
		self.epsilon = self.opt['epsilon']

