import json
from PowerGrid import *


class FactorGraph:
	def __init__(self, auto_lines=False):
		self.vars = {}
		self.funcs = {}
		self.scheduler = None

		self.grid = None
		self.nodes = {}
		self.powerLines = {}
		self.generators = {}
		self.loads = {}
		self.resources = {}
		self.leaves = []
		self.root = None
		self.auto_lines = auto_lines

	def load(self, graph):
		self.grid = json.loads(open(graph, 'r').read())

		for g in self.grid['generators']:
			ge = self.grid['generators'][g]
			self.generators[g] = Generator(g, ge['maxValue'], ge['CO'])

		for r in self.grid['resources']:
			re = self.grid['resources'][r]
			self.resources[r] = Resource(r, re['values'], re['transitions'])

		self.loads = self.grid['loads']

		children = set()
		nodes = set()
		for n in self.grid['nodes']:
			nodes.add(n)
			if 'children' in self.grid['nodes'][n]:
				if len(self.grid['nodes'][n]['children']) == 0:
					self.leaves.append(n)
				else:
					for c in self.grid['nodes'][n]['children']:
						children.add(c)
			else:
				self.leaves.append(n)

		self.root = list(nodes - children)[0]
		if len(nodes - children) > 1:
			raise Exception('Error: More than one root found.')

		for n in self.grid['nodes']:
			# looking for parent of node n
			parent = []
			for p in self.grid['nodes']:
				if 'children' in self.grid['nodes'][p]:
					if n in self.grid['nodes'][p]['children']:
						parent.append(p)

			if len(parent) > 1:
				raise Exception('Error: Graph is not acyclic.')

			if len(parent) == 1:
				parent = parent[0]
			else:
				parent = None

			children = None
			if 'children' in self.grid['nodes'][n]:
				children = self.grid['nodes'][n]['children']

			generators = []
			if 'generators' in self.grid['nodes'][n]:
				generators = self.grid['nodes'][n]['generators']

			resources = []
			if 'resources' in self.grid['nodes'][n]:
				resources = self.grid['nodes'][n]['resources']

			loads = []
			if 'loads' in self.grid['nodes'][n]:
				loads = {l: self.loads[l] for l in self.grid['nodes'][n]['loads']}

			self.nodes[n] = RelayNode(n, parent, children, generators, resources, loads)

		for pl in self.grid['powerLines']:
			a = self.grid['powerLines'][pl]['from']
			b = self.grid['powerLines'][pl]['to']

			self.powerLines[(a, b)] = {'id': pl, 'capacity': self.grid['powerLines'][pl]['capacity']}

		# Factor graph elements
		self.funcs = [n for n in self.nodes]

		for g in self.generators:
			self.vars[g] = {}
			self.vars[g]['domain'] = range(self.generators[g].maxValue) + [self.generators[g].maxValue]
			self.vars[g]['value'] = 0
			self.vars[g]['size'] = self.generators[g].maxValue + 1

		if not self.auto_lines:
			for l in self.powerLines:
				self.vars[l] = {}
				self.vars[l]['value'] = 0
				self.vars[l]['size'] = self.powerLines[l]['capacity'] * 2 + 1
				domain = range(self.powerLines[l]['capacity']) + [self.powerLines[l]['capacity']]
				domain.reverse()
				self.vars[l]['domain'] = [d * -1 for d in domain[:-1]]
				self.vars[l]['domain'] += domain

	def get_value(self, name):
		if name in self.generators:
			value = self.vars[name]['domain'][self.vars[name]['value']]
		elif name in self.powerLines:
			if self.auto_lines:
				pass
			else:
				value = self.vars[name]['domain'][self.vars[name]['value']]
		elif name in self.funcs:
			sum_loads = sum(self.nodes[name].loads.values())
			sum_generators = sum([self.vars[g]['value'] for g in self.nodes[name].generators])
			sum_resources = sum([self.resources[r].getValue(self.scheduler.time) for r in self.nodes[name].resources])
			lines = 0
			if self.nodes[name].parent is not None:
				lines += self.get_power_line_value(name, self.nodes[name].parent) * -1
			for c in self.nodes[name].children:
				lines += self.get_power_line_value(name, c)
			if sum_loads + sum_generators + sum_resources + lines == 0:
				value = sum([vars[g]['value'] * self.nodes[name].generators[g].CO * -1 for g in self.nodes[name].generators])
			else:
				value = float("-inf")
		else:
			raise Exception('Invalid function of variable.')

		return value

	def get_power_line_value(self, n1, n2):
		line = (n1, n2)
		rline = (n2, n1)
		if line in self.vars:
			value = self.vars[line]['value']
		elif rline in self.vars:
			value = self.vars[rline]['value']
		else:
			raise Exception('Invalid power line.')

		return value

	def get_neighbour_variables(self, var):
		nvars = set()
		for f in self.vars[var]['functions']:
			for v in self.funcs[f]['variables']:
				if v != var:
					nvars.add(v)
		return list(nvars)

	def reset(self):
		for v in self.vars:
			self.vars[v]['value'] = 0
