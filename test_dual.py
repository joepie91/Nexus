import application
import threading, logging

class ApplicationThread(threading.Thread):
	def __init__(self, name, args, hook):
		threading.Thread.__init__(self)
		self._name = name
		self._args = args
		self._hook = hook
		
	def run(self):
		application.run(self._args, self._hook)

class Hook(object):
	def write(self, data, *args, **kwargs):
		lines = data.strip().split("\n")
		for line in lines:
			print "[%s] %s" % (self._name, line)
		
def logger_hook(level, format_, target):
	logger = logging.getLogger()
	logger.setLevel(level)
	
	handler = logging.StreamHandler(stream=target)
	handler.setLevel(level)
	handler.setFormatter(logging.Formatter(format_))
	
	logger.addHandler(handler)

#hook = Hook()
#logger_hook(logging.DEBUG, "[%(name)s] %(asctime)s - %(levelname)s - %(message)s", hook)

t1 = ApplicationThread("node1", ["--debug", "--config", "test/node1.yaml"], "node1")
t2 = ApplicationThread("node2", ["--debug", "--config", "test/node2.yaml"], "node2")

t1.start()
t2.start()
