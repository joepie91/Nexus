import yaml, glob, os, logging

from util import dict_combine_recursive

class ConfigurationError(Exception):
	pass

class ConfigurationReader(object):
	def __init__(self, file_):
		self.sources = []
		self.configdata = self.read_config(file_)
		self.config_includes(self.configdata)
		
		self.process_config(self.configdata)
		
	def read_config(self, file_):
		try:
			# File-like object
			data = file_.read()
			self.sources.append(":local:")
		except AttributeError, e:
			# Filename
			f = open(file_, "r")
			data = f.read()
			f.close()
			self.sources.append(file_)
		
		return yaml.safe_load(data)
	
	def process_config(self, configdata):
		self.config_identity(configdata)
		self.config_nodes(configdata)
		self.config_package_settings(configdata)
		
	def config_identity(self, configdata):
		try:
			self.uuid = configdata['self']['uuid']
			logging.debug("Own UUID is %s" % self.uuid)
		except KeyError, e:
			raise ConfigurationError("A UUID for the node ('self') must be specified.")
			
		try:
			self.pubkey = configdata['self']['pubkey']
			logging.debug("Own pubkey is %s" % self.pubkey)
		except KeyError, e:
			raise ConfigurationError("You must specify a public key for this node.")
			
		try:
			self.privkey = configdata['self']['privkey']
			logging.debug("Own privkey is %s" % self.privkey)
		except KeyError, e:
			raise ConfigurationError("You must specify a private key for this node.")
			
		try:
			self.database = configdata['self']['database']
		except KeyError, e:
			self.database = "node.db"
			
		logging.debug("Database location is %s" % self.database)
		
	def config_nodes(self, configdata):
		try:
			self.nodes = configdata['nodes']
		except KeyError, e:
			self.nodes = {} # Optional
		
		for uuid, node in self.nodes.iteritems():
			if "host" not in node:
				raise ConfigurationError("Hostname is missing for node %s." % uuid)
			if "port" not in node:
				raise ConfigurationError("Port is missing for node %s." % uuid)
			if "pubkey" not in node:
				raise ConfigurationError("Public key is missing for node %s." % uuid)
			if "permissions" not in node:
				node['permissions'] = [] # Optional
			if "override" not in node:
				node['override'] = False
				
			logging.debug("Node %s : Hostname %s, port %s, pubkey %s, permissions %s" % (uuid, node["host"], node["port"], node["pubkey"], "|".join(node["permissions"])))
			
	def config_package_settings(self, configdata):
		try:
			self.package_settings = configdata['package-settings']
			
			for key in self.package_settings:
				logging.debug("Package settings found for package %s" % key)
		except KeyError, e:
			self.package_settings = {} # Optional
			
	def config_includes(self, configdata):
		try:
			include_list = configdata['include']
		except KeyError, e:
			return # Optional
		
		try:
			include_list.append
		except:
			include_list = [include_list]
			
		for include in include_list:
			for file_ in glob.iglob(os.path.expanduser(include)):
				if file_ not in self.sources:
					self.sources.append(file_)
					includedata = self.read_config(file_)
					self.configdata = dict_combine_recursive(self.configdata, includedata)
					self.config_includes(includedata)
