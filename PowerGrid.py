import util


class RelayNode:
	def __init__(self, id, parent, children, generators, resources, loads, powerLines, parentPL, childrenPL):
		self.id = id
		self.parent = parent
		self.children = children
		self.generators = generators
		self.loads = loads
		self.resources = resources
		self.powerLines = powerLines
		self.parentPL = parentPL
		self.childrenPL = childrenPL


class Generator:
	def __init__(self, id, maxValue, CO):
		self.id = id
		self.maxValue = maxValue
		self.CO = CO


class Resource:
	def __init__(self, id, values, transitions):
		self.id = id
		self.values = values
		self.transitions = [[(p[0], p[1]) for p in t] for t in transitions]
		self.periodLen = len(values)

	def getValue(self, time):
		timeStep = time % self.periodLen
		nextTimeStep = (time + 1) % self.periodLen
		valueIndex = util.chooseFromDistribution(self.transitions[timeStep])
		if valueIndex is not None:
			value = self.values[nextTimeStep][valueIndex]
		else:
			value = 0
		return value
