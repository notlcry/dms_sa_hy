from threading import Thread
from yapsy.IPlugin import IPlugin


class IMultithreadChildPlugin(IPlugin, Thread):
	"""
	Base class for multiprocessed plugin.
	"""

	def __init__(self, parent_pipe):
		self.parent_pipe = parent_pipe
		IPlugin.__init__(self)
		Thread.__init__(self)
                self.daemon = True

	def run(self):
		"""
		Override this method in your implementation
		"""
		return
