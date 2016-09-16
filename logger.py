class Logger:
	def __init__(self, debugLevel, logFile=None, stderr=False):
		self.logFile = logFile
		self.debugLevel = debugLevel
		self.stderr = stderr

		if logFile is not None:
			self.logFile = open(logFile, 'w')

	def log(self, msg, level):
		pass
