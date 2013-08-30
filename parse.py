import sys

class Element(object):
	def __init__(self):
		self.outputs = []
		
	def display(self, indent):
		print ("\t" * indent) + self.get_description()
		for output in self.outputs:
			output.display(indent + 1)
	
class Bin(Element):
	def __init__(self, name):
		Element.__init__(self)
		self.name = name
		
	def get_description(self):
		return "[Bin] %s" % self.name
	
class Rule(Element):
	def __init__(self, input_):
		Element.__init__(self)
		self.input_ = input_
		
	def process(self, message):
		self.forward(message)
		
	def forward(self, message):
		for output in self.outputs:
			output.process(message)
	
class Filter(Rule):
	def __init__(self, input_, rule):
		Rule.__init__(self, input_)
		# TODO: Filter parsing loop goes here
		self.rule = rule
		
	def get_description(self):
		return "[Filter] %s" % self.rule

class BinReference(Rule):
	def __init__(self, input_, name):
		Rule.__init__(self, input_)
		self.bin_name = name
		
	def get(self):
		try:
			return bins[self.bin_name]
		except KeyError, e:
			new_bin = Bin(self.bin_name)
			bins[self.bin_name] = new_bin
			return new_bin
			
	def get_description(self):
		return "[BinRef] %s" % self.bin_name

class NodeReference(Rule):
	def __init__(self, input_, name):
		Rule.__init__(self, input_)
		self.node_name = name
		
	def get_description(self):
		return "[NodeRef] %s" % self.node_name
		
class MethodReference(Rule):
	def __init__(self, input_, name):
		Rule.__init__(self, input_)
		self.method_name = name
		
	def get_description(self):
		return "[MethodRef] %s" % self.method_name
		
class DistributorReference(Rule):
	def __init__(self, input_, name, args):
		Rule.__init__(self, input_)
		self.distributor_name = name
		self.args = args
		
	def get_description(self):
		return "[DistRef] %s" % self.distributor_name

def create_rule(buff, input_):
	buff = buff.strip()
	if buff[0] == "*":
		# Node reference
		new_obj = NodeReference(input_, buff[1:])
	elif buff[0] == "@":
		# Method call
		new_obj = MethodReference(input_, buff[1:])
	elif buff[0] == "#":
		# Bin reference
		new_obj = BinReference(input_, buff[1:])
	elif buff[0] == ":":
		# Distributor
		if "(" in buff and buff[-1:] == ")":
			name, arglist = buff[1:-1].split("(", 1)
			args = [x.strip() for x in arglist.split(",")]
		else:
			name = buff[1:]
			args = []
		new_obj = DistributorReference(input_, name, args)
	else:
		# Filter
		new_obj = Filter(input_, buff)
		
	input_.outputs.append(new_obj)
	return new_obj

f = open(sys.argv[1])
rulebook = f.read()
f.close()
rulebook_length = len(rulebook)

# Main parsing loop
idx = 0
tab_count = 0
current_level = 0
current_rule = {}
target_rule = None
statement_cache = None
new_line = True
multiple_statements = False
buff = ""
bins = {}

while idx < rulebook_length:
	char = rulebook[idx]
	
	if char == "\t":
		if buff == "":
			new_line = True
			tab_count += 1
		else:
			buff += char
	else:
		if new_line == True:
			if tab_count > current_level + 1:
				raise Exception("Incorrect indentation")
			else:
				try:
					target_rule = current_rule[tab_count - 1]
				except KeyError, e:
					pass# FIXME: raise Exception("Incorrect indentation (bug?)")
			
			if rulebook[idx:idx+2] == "=>":
				# Skip over this, it's optional at the start of a line
				idx += 2
				continue
				
			new_line = False
		
		if char == "\r":
			pass #ignore
		elif char == "\n":
			# Process
			if buff.strip() == "":
				# Skip empty lines, we don't care about them
				idx += 1
				tab_count = 0
				continue
				
			current_level = tab_count
			tab_count = 0
			
			if current_level == 0:
				bin_name = buff.strip()
				new_bin = Bin(bin_name)
				current_rule[current_level] = new_bin
				bins[bin_name] = new_bin
			else:
				if multiple_statements == True:
					new_rule = create_rule(buff, statement_cache)
				else:
					new_rule = create_rule(buff, current_rule[current_level - 1])
					
				current_rule[current_level] = new_rule
				
			buff = ""
			new_line = True
			multiple_statements = False
		elif char == "=" and rulebook[idx + 1] == ">":
			# Next rule, same line!
			if multiple_statements == True:
				statement_cache = create_rule(buff, statement_cache)
			else:
				multiple_statements = True
				statement_cache = create_rule(buff, current_rule[tab_count - 1])
			
			buff = ""
			idx += 1 # We read one extra character ahead
		else:
			buff += char
			
	idx += 1
	# TODO: detect infinite loops via bins!

for bin_name, bin_ in bins.iteritems():
	bin_.display(0)
