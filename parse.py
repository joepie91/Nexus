import sys
from collections import defaultdict

# TODO: Keep trail of message travelling through the rules

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
		self.rule = rule
		
		# Rules:
		#  Boolean 'and' has precedence over 'or'
		#  Enclosure in parentheses means creating a new FilterExpressionGroup
		#  Having 'and' and 'or' operators in the same group means a new FilterExpressionGroup is created for every 'and' chain, to retain precedence
		#  Variable accessors are prefixed with $
		#  Strings are enclosed in "quotes"
		
		rule_length = len(rule)
		idx = 0
		buff = ""
		in_expression = False
		current_element = {}
		element_list = defaultdict(list)
		operator_list = defaultdict(list)
		current_depth = 0
		
		while idx < rule_length:
			char = rule[idx]
			print len(buff), len(rule), idx, buff
			if char == "(" and in_expression == False:
				# New group encountered
				group = FilterExpressionGroup()
				current_element[current_depth] = group
				print "START GROUP %d" % current_depth
				current_depth += 1
			elif char == ")" and in_expression == False:
				# End statement, Process list of elements
				element_list[current_depth].append(create_filter_expression(buff))
				# Add elements to group object
				for el in element_list[current_depth]:
					current_element[current_depth - 1].add(el)
				# Process operators
				if len(element_list[current_depth]) > 1:
					# Check if the operators vary
					operators = operator_list[current_depth]
					operator_discrepancy = not all(operators[0] == x for x in operators)
					
					if operator_discrepancy:
						# We'll need to find the 'and' chains and push them into separate groups
						print "OPERATOR DISCREPANCY"
					
					current_element[current_depth - 1].relation = operator_list[current_depth][0]
					element_list[current_depth - 1].append(current_element[current_depth - 1])
					operator_list[current_depth] = [] # Clear out list to prevent working with stale data
					
				print "-- GR: %s" % current_element[current_depth - 1]
				buff = ""
				current_depth -= 1
				print "END GROUP %d" % current_depth
			elif char == '"':
				in_expression = not in_expression
				buff += '"'
			elif not in_expression and char == "o" and idx + 2 < rule_length and rule[idx+1:idx+2] == "r" and len(buff) > 0 and (buff[-1] == " " or buff[-1] == ")"):
				# End statement, Boolean OR
				if buff.strip() != "":
					element_list[current_depth].append(create_filter_expression(buff))
				operator_list[current_depth].append(OR)
				buff = ""
				idx += 1 # We read ahead one position extra
			elif not in_expression and char == "a" and idx + 3 < rule_length and rule[idx+1:idx+3] == "nd" and len(buff) > 0 and (buff[-1] == " " or buff[-1] == ")"):
				# End statement, Boolean AND
				if buff.strip() != "":
					element_list[current_depth].append(create_filter_expression(buff))
				operator_list[current_depth].append(AND)
				buff = ""
				idx += 2 # We read ahead two positions extra
			else:
				buff += char
				
			idx += 1
		
		if current_depth > 0:
			raise Exception("Missing %d closing parenthese(s)." % current_depth)
		elif current_depth < 0:
			raise Exception("Missing %d opening parenthese(s)." % (0 - current_depth))
			
		if buff.strip() != "":
			element_list[current_depth].append(create_filter_expression(buff))
			
		if len(element_list[current_depth]) > 1:
			# Multiple elements, need to encapsulate in a group
			new_group = create_group(element_list[current_depth], operator_list[current_depth])
			
		# If there's anything left in the buffer, it's probably a statement we still need to process.
		print repr(element_list)
		
	def get_description(self):
		return "[Filter] %s" % self.rule

def create_group(elements, operators):
	group = FilterExpressionGroup()

def create_filter_expression(buff):
	# TODO: Use shlex split because of spaces in strings?
	left, operator, right = [x.strip() for x in buff.split(None, 2)]
	
	if left[0] == '"' and left[-1] == '"':
		left_obj = FilterExpressionString(left[1:-1])
	elif left[0] == "$":
		if "[" in left[1:] and left[-1] == "]":
			name, scope = left[1:-1].split("[", 1)
		else:
			name = left[1:]
			scope = None
			
		left_obj = FilterExpressionVariable(name, scope)
	else:
		raise Exception("Unrecognized operand type") # No other types supported yet...
	
	if right[0] == '"' and right[-1] == '"':
		right_obj = FilterExpressionString(right[1:-1])
	elif right[0] == "$":
		if "[" in right[1:] and right[-1] == "]":
			name, scope = right[1:-1].split("[", 1)
		else:
			name = right[1:]
			scope = None
			
		right_obj = FilterExpressionVariable(name, scope)
	else:
		raise Exception("Unrecognized operand type") # No other types supported yet...
	
	operators = {
		"=": EQUALS,
		"==": EQUALS,
		"!=": NOT_EQUALS,
		">": MORE_THAN,
		"<": LESS_THAN,
		">=": MORE_THAN_OR_EQUALS,
		"<=": LESS_THAN_OR_EQUALS,
		"has": HAS
	}
	
	try:
		operator_type = operators[operator]
	except KeyError, e:
		raise Exception("Invalid operator")
	
	expression = FilterExpression(left_obj, operator_type, right_obj)
	return expression
	# Broken?
	#print expression

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

NONE = 0
AND = 1
OR = 2

EQUALS = 3
NOT_EQUALS = 4
LESS_THAN = 5
MORE_THAN = 6
LESS_THAN_OR_EQUALS = 7
MORE_THAN_OR_EQUALS = 8
HAS = 9

class FilterExpression(object):
	def __init__(self, left, operator, right):
		self.left = left
		self.operator = operator
		self.right = right
		
	def evaluate(self, message):
		if self.operator == EQUALS:
			return (self.left == self.right)
		elif self.operator == NOT_EQUALS:
			return (self.left != self.right)
		elif self.operator == LESS_THAN:
			return (self.left < self.right)
		elif self.operator == MORE_THAN:
			return (self.left > self.right)
		elif self.operator == LESS_THAN_OR_EQUALS:
			return (self.left <= self.right)
		elif self.operator == MORE_THAN_OR_EQUALS:
			return (self.left >= self.right)
		elif self.operator == HAS:
			return False  # TODO: Implement array lookup?
		else:
			# TODO: Log error
			return False
			
	def __repr__(self):
		if self.operator == EQUALS:
			opname = "EQUALS"
		elif self.operator == NOT_EQUALS:
			opname = "NOT EQUALS"
		elif self.operator == LESS_THAN:
			opname = "LESS THAN"
		elif self.operator == MORE_THAN:
			opname = "MORE THAN"
		elif self.operator == LESS_THAN_OR_EQUALS:
			opname = "LESS THAN OR EQUAL"
		elif self.operator == MORE_THAN_OR_EQUALS:
			opname = "MORE THAN OR EQUAL"
		else:
			opname = "?"
			
		return "<FE %s [%s] %s>" % (repr(self.left), opname, repr(self.right))
	
class FilterExpressionGroup(object):
	def __init__(self):
		self.elements = []
		self.relation = NONE
	
	def add(self, element):
		self.elements.append(element)
	
	def evaluate(self, message):
		if self.relation == AND:
			for element in self.elements:
				if element.evaluate() != True:
					return False
			return True
		elif self.relation == OR:
			for element in self.elements:
				if element.evaluate() == True:
					return True
			return False
		else:
			# TODO: Log error
			return False
			
	def __repr__(self):
		if self.relation == AND:
			relname = "AND"
		elif self.relation == OR:
			relname = "OR"
		else:
			relname = "?"
		return "<FEGroup %s (%s)>" % (relname, ", ".join(repr(x) for x in self.elements))

class FilterExpressionElement(object):
	pass
	
class FilterExpressionVariable(FilterExpressionElement):
	def __init__(self, scope, name=None):
		self.scope = scope
		self.name = name
		# TODO: name path parsing
		
	def get_value(self, message):
		return False # TODO: grab correct value
		
	def __repr__(self):
		return "<FEVar %s/%s>" % (self.scope, self.name)
	
class FilterExpressionString(FilterExpressionElement):
	def __init__(self, string):
		self.string = string
		
	def get_value(self, message):
		return self.string
		
	def __repr__(self):
		return "<FEString \"%s\">" % self.string

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
			
			if rulebook[idx:idx+2] == "=>":
				# Skip over this, it's optional at the start of a line
				idx += 2
				continue
				
			new_line = False
		
		if char == "\r":
			idx += 1
			continue # Ignore, we don't want carriage returns
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
			# TODO: add entire chunks at once for speed
			buff += char
			
	idx += 1
	# TODO: detect infinite loops via bins!

for bin_name, bin_ in bins.iteritems():
	pass#bin_.display(0)
