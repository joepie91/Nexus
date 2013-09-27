import sqlite3

class Database(object):
	def __init__(self, dbpath = "node.db"):
		self.conn = sqlite3.connect(dbpath)
		self.conn.row_factory = Row
		self.tables = {}
	
	def _get_cursor(self):
		return self.conn.cursor()
		
	def _table_create_nodes(self):
		self.query("CREATE TABLE IF NOT EXISTS nodes (`id` INTEGER PRIMARY KEY, `uuid` TEXT, `host` TEXT, `port` NUMERIC, `pubkey` TEXT, `presupplied` NUMERIC, `attributes` NUMERIC);")
	
	def _get_table(self, name, in_memory=False, forced=False):
		if in_memory == True:
			try:
				# Only create a new MemoryTable if one doesn't already exist
				create_new = forced or not isinstance(self.tables[name], MemoryTable)
			except KeyError, e:
				create_new = True
		else:
			try:
				self.tables[name]
				create_new = forced or False
			except KeyError, e:
				create_new = True
		
		if create_new == False:
			return self.tables[name]
		else:
			if in_memory == True:
				new_table = MemoryTable(self, name)
			else:
				new_table = DatabaseTable(self, name)
				
			self.tables[name] = new_table
			return new_table
	
	def __getitem__(self, key):
		return self.get_database_table(key)
		
	def get_database_table(self, name):
		return self._get_table(name, in_memory=False)
	
	def get_memory_table(self, name):
		return self._get_table(name, in_memory=True)
	
	def query(self, query, params = [], commit=False):
		print "QUERY: %s" % query
		print "PARAMS: %s" % repr(params)
		
		cur = self._get_cursor()
		cur.execute(query, params)
		
		if commit == True:
			self.conn.commit()
			
		return cur

	def setup(self):
		self._table_create_nodes()

class Row(object):
	def __init__(self, cursor=None, row=None):
		self._commit_buffer = {}
		self._data = {}
		
		if cursor is None and row is None:
			self._new = True
		else:
			self._new = False
			
			for index, column in enumerate(cursor.description):
				self._data[column[0]] = row[index]
	
	def __getitem__(self, key):
		return self._data[key]
	
	def __setitem__(self, key, value):
		self._commit_buffer[key] = value
	
	def _clear_buffer(self):
		self._commit_buffer = {}
	
	def commit(self):
		# Commit to database
		if len(self._commit_buffer) > 0:
			statement_list = ", ".join("`%s` = ?" % key for key in self._commit_buffer.keys())
			query = "UPDATE %s SET %s WHERE `id` = %s" % (self._nexus_table, statement_list, self['id'])  # Not SQLi-safe!
			self._nexus_db.query(query, params=self._commit_buffer.values(), commit=True)
			
			# Update locally
			for key, value in self._commit_buffer.iteritems():
				self._data[key] = value
				
		# Clear out commit buffer
		self._clear_buffer()
		
	def rollback(self):
		self._clear_buffer()

class Table(object):
	def __init__(self, database, table_name):
		# You should never construct this directly!
		self.db = database
		self.table = table_name
	
	def _process_insert(self, value, key=None):
		if key is not None:
			value['id'] = key
			
		column_list = ", ".join("`%s`" % name for name in value._commit_buffer.keys())
		sub_list = ", ".join("?" for name in value._commit_buffer.keys())
		query = "INSERT INTO %s (%s) VALUES (%s)" % (self.table, column_list, sub_list)  # Not SQLi-safe!
		
		result = self.db.query(query, params=value._commit_buffer.values(), commit=True)
		
		value._new = False
		
		return result.lastrowid
	
	def _try_set(self, key, value, cache):
		if key in cache:
			raise TypeError("A row with the given ID already exists. Either edit the existing one, or append a new row using append().")
		else:
			try:
				self._process_insert(value, key)
			except sqlite3.IntegrityError, e:
				raise TypeError("A row with the given ID already exists. Either edit the existing one, or append a new row using append().")
	
	def append(self, value):
		return self._process_insert(value)
		
class DatabaseTable(Table):
	def __init__(self, database, table_name):
		Table.__init__(self, database, table_name)
		self._cache = {}
	
	def _process_insert(self, value, key=None):
		rowid = Table._process_insert(self, value, key)
		self._cache[rowid] = value
		return rowid
	
	def __getitem__(self, key):
		try:
			return self._cache[key]
		except KeyError, e:
			result = self.db.query("SELECT * FROM %s WHERE `id` = ?" % self.table, params=(key,))
			
			if result is None:
				raise KeyError("No row with that ID was found in the table.")
			else:
				row = result.fetchone()
				row._nexus_db = self.db
				row._nexus_table = self.table
				row._nexus_type = "database"
				self._cache[key] = row
				return row
				
	def __setitem__(self, key, value):
		self._try_set(key, value, self._cache)

class MemoryTable(Table):
	def __init__(self, database, table_name):
		Table.__init__(self, database, table_name)
		self.data = {}
		
		result = database.query("SELECT * FROM %s" % table_name)  # Not SQLi-safe!
		
		for row in result:
			row._nexus_db = database
			row._nexus_table = table_name
			row._nexus_type = "memory"
			self.data[row['id']] = row
			
	def _process_insert(self, value, key=None):
		rowid = Table._process_insert(self, value, key)
		self.data[rowid] = value
		return rowid
			
	def __getitem__(self, key):
		return self.data[key]
		
	def __setitem__(self, key, value):
		self._try_set(key, value, self.data)
	

if __name__ == "__main__":
	# Testing code
	db = Database()
	db.setup()
	table = db.get_database_table("nodes")
	
	new_row = Row()
	new_row['uuid'] = "abc"
	new_row['host'] = "def"
	new_row['port'] = 123
	
	#table.append(new_row)
	table[10] = new_row
	
	
	#table[1]['uuid'] = "bleep"
	#table[1]['host'] = "bloop"
	#table[1].commit()
	#table[1]['port'] = 1234
	#table[1].commit()




"""

# This is a complete mess. Looks like subclassing C extension stuff is a bad idea.

class Row(sqlite3.Row):
	def __init__(self, cursor, row):
		sqlite3.Row.__init__(self, cursor, row)
		#super(sqlite3.Row, self).__init__(cursor, row)  # This segfaults!
		self._commit_buffer = {}
		self._commit_data = {}
		
		# Yes, this will make lookup slower. No real solution for this for now.
		for key in self.keys():
			self._commit_data[key] = self[key]
		
		self.__getitem__ = self._nexus_getitem
	
	def _nexus_getitem(self, key):
		# FIXME: Currently, only when using dict access, the data modified through a commit will be accessible.
		#try:
		print "GET %s" % key
		return self._commit_data[key]
		#except KeyError, e:
		#	#return sqlite3.Row.__get__(self, key)
		#	print super(Row, self).__get__(key)
		#	return super(Row, self).__get__(key)
	
	def __setitem__(self, key, value):
		self._commit_buffer[key] = value
	
	def _clear_buffer(self):
		self._commit_buffer = {}
	
	def commit(self):
		# Commit to database
		statement_list = ", ".join("`%s` = ?" % key for key in self._commit_buffer.keys())
		query = "UPDATE %s SET %s WHERE `id` = %s" % (self._nexus_table, statement_list, self['id'])  # Not SQLi-safe!
		print query
		print self._commit_buffer.values()
		#self._nexus_db.query(query, params=self._commit_buffer.values())
		
		# Update locally
		for key, value in self._commit_buffer.iteritems():
			self._commit_data[key] = value
			
		# Clear out commit buffer
		self._clear_buffer()
		
	def rollback(self):
		self._clear_buffer()
"""
