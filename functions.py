class Functions1:

	def __init__(self, fg):
		self.fg = fg

	def v(self, var):
		return self.fg.get_value(var)

	def f1(self):
		return 3 * self.v("x1")**3

	def f2(self):
		return 4 * self.v("x1")**4 - self.v("x2")**2

	def f3(self):
		x3 = self.v("x3")
		return -1 * (x3**3 + x3)

	def f4(self):
		return self.v("x2")**4 + 1/self.v("x3")**2

	def f5(self):
		x3 = self.v("x3")
		return 3 * x3 + 1/x3


class Functions2:

	def __init__(self, fg):
		self.fg = fg
		self.a1 = 0
		self.a2 = 0
		self.a3 = 0

	def v(self, var):
		return self.fg.get_value(var)

	def f1(self):
		return -(self.v("x1") + self.a2*2 - 5)**2 + 3

	def f2(self):
		return -(self.v("x1") - 5)**2 - (self.v("x2") - 2)**2 - self.a1

	def f3(self):
		x3 = self.v("x2")
		return -(x3 - 5)**4 - self.a3**2

	def f4(self):
		return -(self.v("x2") - 5)**2 - (self.v("x3") - 2)**2

	def f5(self):
		x3 = self.v("x3")
		return -(x3 - 5) ** 2 - self.a2

	def change(self):
		self.a1 = 0
		self.a2 = 10
		self.a3 = 20
