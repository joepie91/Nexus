from constants import *
from itertools import groupby
from collections import defaultdict
from exceptions import *

def parse(input_):
	# Rules:
	#  Boolean 'and' has precedence over 'or'
	#  Enclosure in parentheses means creating a new FilterExpressionGroup
	#  Having 'and' and 'or' operators in the same group means a new FilterExpressionGroup is created for every 'and' chain, to retain precedence
	#  Variable accessors are prefixed with $
	#  Strings are enclosed in "quotes"
	
	rule_length = len(input_)
	idx = 0
	buff = ""
	in_expression = False
	current_element = {}
	element_list = defaultdict(list)
	operator_list = defaultdict(list)
	current_depth = 0
	
	while idx < rule_length:
		char = input_[idx]
		
		if char == "(" and in_expression == False:
			# New group encountered
			#print "START GROUP %d" % current_depth
			current_depth += 1
		elif char == ")" and in_expression == False:
			# End statement, Process list of elements
			element_list[current_depth].append(create_filter_expression(buff))
			# Add elements to group object
			group = create_group(element_list[current_depth], operator_list[current_depth])
			element_list[current_depth - 1].append(group)
			
			element_list[current_depth] = []
			operator_list[current_depth] = [] # Clear out lists to prevent working with stale data
				
			#print "-- GR: %s" % group
			buff = ""
			current_depth -= 1
			#print "END GROUP %d" % current_depth
		elif char == '"':
			in_expression = not in_expression
			buff += '"'
		elif not in_expression and char == "o" and idx + 2 < rule_length and input_[idx+1:idx+2] == "r" and len(buff) > 0 and (buff[-1] == " " or buff[-1] == ")"):
			# End statement, Boolean OR
			if buff.strip() != "":
				element_list[current_depth].append(create_filter_expression(buff))
			operator_list[current_depth].append(OR)
			buff = ""
			idx += 1 # We read ahead one position extra
		elif not in_expression and char == "a" and idx + 3 < rule_length and input_[idx+1:idx+3] == "nd" and len(buff) > 0 and (buff[-1] == " " or buff[-1] == ")"):
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
		raise MissingParenthesesError("Missing %d closing parenthese(s)." % current_depth)
	elif current_depth < 0:
		raise MissingParenthesesError("Missing %d opening parenthese(s)." % (0 - current_depth))
	
	# If there's anything left in the buffer, it's probably a statement we still need to process.	
	if buff.strip() != "":
		element_list[current_depth].append(create_filter_expression(buff))
		
	if len(element_list[current_depth]) > 1:
		# Multiple elements, need to encapsulate in a group
		root_element = create_group(element_list[current_depth], operator_list[current_depth])
	elif len(element_list[current_depth]) == 1:
		root_element = element_list[current_depth][0]
	else:
		raise MissingRootElementError("No root element could be determined in the expression.")
		
	return root_element

def create_group(elements, operators):
	group = FilterExpressionGroup()
		
	# Process operators
	if len(elements) > 1:
		# Check if the operators vary
		operator_discrepancy = (len(set(operators)) > 1)
		
		if operator_discrepancy:
			# We'll need to find the 'and' chains and push them into separate child groups
			idx = 0
			sieve = [True for x in xrange(0, len(elements))]
			final_list = []
			
			for operator, items in groupby(operators):
				items = list(items)
				
				start = idx
				end = idx + len(items) + 1
				relevant_elements = elements[start:end]
				
				if operator == AND:
					for i in xrange(start, end):
						# Mark as processed
						sieve[i] = False
					for i in [x for x in xrange(0, end) if sieve[x] is True]:
						final_list.append(elements[i])
						sieve[i] = False
					final_list.append(create_group(relevant_elements, [AND for x in xrange(0, end - start)]))
					
				idx += len(items)
				
			# Add the remaining OR items after the last AND chain
			for i in [x for x in xrange(0, len(elements)) if sieve[x] is True]:
				final_list.append(elements[i])
			
			for element in final_list:
				group.add(element)
				
			group.relation = OR  # Hardcoded, because all AND chains are taken care of above...
		else:
			for element in elements:
				group.add(element)
			group.relation = operators[0]
	else:
		group.add(elements[0])
		
	return group

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
		raise InvalidOperandError("Unrecognized operand type.") # No other types supported yet...
	
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
		raise InvalidOperandError("Unrecognized operand type.") # No other types supported yet...
	
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
		raise InvalidOperatorError("Unrecognized operator.")
	
	expression = FilterExpression(left_obj, operator_type, right_obj)
	return expression

class FilterExpression(object):
	def __init__(self, left, operator, right):
		self.left = left
		self.operator = operator
		self.right = right
		
	def evaluate(self, message):
		if self.operator == EQUALS:
			return (self.left.value(message) == self.right.value(message))
		elif self.operator == NOT_EQUALS:
			return (self.left.value(message) != self.right.value(message))
		elif self.operator == LESS_THAN:
			return (self.left.value(message) < self.right.value(message))
		elif self.operator == MORE_THAN:
			return (self.left.value(message) > self.right.value(message))
		elif self.operator == LESS_THAN_OR_EQUALS:
			return (self.left.value(message) <= self.right.value(message))
		elif self.operator == MORE_THAN_OR_EQUALS:
			return (self.left.value(message) >= self.right.value(message))
		elif self.operator == HAS:
			if is_instance(self.left, basestring):
				return (self.right.value(message) in self.left.value(message))  # Substring comparison
			else:
				return (self.right.value(message) in self.left.values(message))  # In-array check
		else:
			raise EvaluationError("Unhandled operator encountered during evaluation.")
			
	def __repr__(self):
		return "<FE %s [%s] %s>" % (repr(self.left), self.get_opname(), repr(self.right))
		
	def get_opname(self):
		if self.operator == EQUALS:
			return "EQUALS"
		elif self.operator == NOT_EQUALS:
			return "NOT EQUALS"
		elif self.operator == LESS_THAN:
			return "LESS THAN"
		elif self.operator == MORE_THAN:
			return "MORE THAN"
		elif self.operator == LESS_THAN_OR_EQUALS:
			return "LESS THAN OR EQUAL"
		elif self.operator == MORE_THAN_OR_EQUALS:
			return "MORE THAN OR EQUAL"
		elif self.operator == HAS:
			return "HAS"
		else:
			return "?"
		
	def pretty_print(self, level=0):
		prefix = "\t" * level
		print prefix + "%s %s %s" % (repr(self.left), self.get_opname(), repr(self.right))
	
class FilterExpressionGroup(object):
	def __init__(self):
		self.elements = []
		self.relation = NONE
	
	def add(self, element):
		self.elements.append(element)
	
	def evaluate(self, message):
		if self.relation == AND:
			for element in self.elements:
				if element.evaluate(message) != True:
					return False
			return True
		elif self.relation == OR:
			for element in self.elements:
				if element.evaluate(message) == True:
					return True
			return False
		else:
			raise EvaluationError("Unhandled group relationship encountered during evaluation.")
			
	def __repr__(self):
		return "<FEGroup %s (%s)>" % (self.get_relname(), ", ".join(repr(x) for x in self.elements))
		
	def get_relname(self):
		if self.relation == AND:
			return "AND"
		elif self.relation == OR:
			return "OR"
		else:
			return "?"
		
	def pretty_print(self, level=0):
		prefix = "\t" * level
		
		print prefix + "group[%s] (" % self.get_relname()
		for element in self.elements:
			element.pretty_print(level=(level+1))
		print prefix + ")"

class FilterExpressionElement(object):
	def select_value(self, message, scope, name, multiple=False):
		if scope == "tags":
			return_value = message.tags
		elif scope == "type":
			return_value = message.type_
		elif scope == "source":
			return_value = message.source
		elif scope == "chain":
			return_value = message.chain
		elif scope == "attr":
			return_value = self.select_attribute(message, name, multiple=multiple)
		else:
			raise ScopeError("Invalid scope specified.")
			
		if isinstance(return_value, basestring):
			return return_value
		elif len(return_value) > 0:
			if multiple == False:
				return return_value[0]
			else:
				return return_value
		else:
			raise EvaluationError("No valid value could be found.")
			
	def select_attribute(self, message, query, multiple=False):
		segments = query.split("/")
		current_object = message.data
		
		for segment in segments:
			try:
				current_object = current_object[segment]
			except KeyError, e:
				raise AttributeNameError("Invalid attribute specified.")
				
		return current_object
	
class FilterExpressionVariable(FilterExpressionElement):
	def __init__(self, scope, name=None):
		self.scope = scope
		self.name = name
		# TODO: name path parsing
		
	def value(self, message):
		return self.select_value(message, self.scope, self.name, multiple=False)
	
	def values(self, message):
		return self.select_value(message, self.scope, self.name, multiple=True)
		
	def __repr__(self):
		return "<FEVar %s/%s>" % (self.scope, self.name)
	
class FilterExpressionString(FilterExpressionElement):
	def __init__(self, string):
		self.string = string
		
	def value(self, message):
		return self.string
		
	def values(self, message):
		return [self.string]
		
	def __repr__(self):
		return "<FEString \"%s\">" % self.string
