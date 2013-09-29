import core # Nexus core
import argparse, sys
import logging

def run(args):
	parser = argparse.ArgumentParser(description="Nexus daemon")
	parser.add_argument("-c", "--config", dest="config_file", metavar="PATH", help="specifies the configuration file to use", default="config.yaml")
	parser.add_argument("-d", "--debug", dest="debug_mode", action="store_true", help="enables debugging mode", default=False)
	arguments = parser.parse_args(args)
	
	if arguments.debug_mode == True:
		logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
	else:
		logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
	
	logging.info("Application started")
	
	try:
		config = core.config.ConfigurationReader(arguments.config_file)
	except IOError, e:
		sys.stderr.write("Failed to read configuration file (%s).\nCreate a configuration file that Nexus can access, or specify a different location using the -c switch.\n" % e.strerror)
		exit(1)
		
	logging.info("Read configuration file at %s" % arguments.config_file)
	
	# Connect to node database
	database = core.db.Database(config.database)
	database.setup()
	node_table = database.get_memory_table("nodes")
	
	logging.info("Connected to database at %s" % config.database)
	
	# Read bootstrap/override node data
	for uuid, node in config.nodes.iteritems():
		existing_rows = [dbnode for rowid, dbnode in node_table.data.iteritems() if dbnode['uuid'] == uuid]
		
		if node['override'] == True:
			row = existing_rows[0]
			row['uuid'] = uuid
			row['host'] = node['host']
			row['port'] = node['port']
			row['pubkey'] = node['pubkey']
			row['presupplied'] = 1
			row['attributes'] = 0
			row.commit()
			logging.info("Updated data in database for node using configuration file (%s:%s, %s)" % (node['host'], node['port'], uuid))
		else:
			if len(existing_rows) == 0:
				row = core.db.Row()
				row['uuid'] = uuid
				row['host'] = node['host']
				row['port'] = node['port']
				row['pubkey'] = node['pubkey']
				row['presupplied'] = 1
				row['attributes'] = 0
				database['nodes'].append(row)
				logging.info("Learned about new node from configuration file, inserted into database (%s:%s, %s)" % (node['host'], node['port'], uuid))
			else:
				pass # Already exists and no override flag set, ignore
	
if __name__ == "__main__":
	run(sys.argv[1:])
