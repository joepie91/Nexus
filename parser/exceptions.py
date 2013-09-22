class ParserException(Exception):
	pass
	
class MissingRootElementError(ParserException):
	pass
	
class ParsingSyntaxError(ParserException):
	pass

class RulebookIndentationError(ParsingSyntaxError):
	pass

class MissingParenthesesError(ParsingSyntaxError):
	pass

class InvalidOperatorError(ParsingSyntaxError):
	pass
	
class EvaluationError(ParserException):
	pass

class ScopeError(EvaluationError):
	pass
	
class AttributeNameError(EvaluationError):
	pass
