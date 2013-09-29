def dict_combine_recursive(a, b):
	# Based on http://stackoverflow.com/a/8725321
	if a is None: return b
	if b is None: return a
	if isinstance(a, list) and isinstance(b, list):
		return list(set(a + b))
	elif isinstance(a, dict) and isinstance(b, dict):
		keys = set(a.iterkeys()) | set(b.iterkeys())
		return dict((key, dict_combine_recursive(a.get(key), b.get(key))) for key in keys)
	else:
		return b
