class RelayNode:
	def __init__(self, id, parent, children, generators, resources, loads, powerGrid, opt, debugLevel):
		self.id = id
		self.parent = parent
		self.children = children
		self.pg = powerGrid
		self.generators = { g:self.pg.generators[g] for g in generators }
		self.loads = { l:self.pg.loads[l] for l in loads }
		self.resources = { r:self.pg.resources[r] for r in resources }


class Generator:
	def __init__(self, maxValue):
		self.value = 0
		self.maxValue = maxValue
		self.actions = [-1, 0, 1]

	def increase(self):
		if self.value + 1 <= self.maxValue:
			self.value += 1

	def decrease(self):
		if self.value - 1 >= 0:
			self.value -= 1

	def getValue(self):
		return self.value

	def getActions(self):
		return [ a for a in self.actions if (self.value + a >= 0) ]


class Resource:
	def __init__(self, values, prob, distribution):
		self.values = values
		self.distribution = distribution
		self.index = 0
		self.distributionIterator = 0
		self.maxIteration = len(self.distribution)
		self.prob = prob

	def getProbeblisticValue(self):
		r = self.distribution[self.distributionIterator]
		self.distributionIterator += 1
		if self.distributionIterator == self.maxIteration:
			self.distributionIterator = 0
		if r < self.prob:
			return self.values[0]
		return 0

	def getValue(self):
		return self.values[self.index]