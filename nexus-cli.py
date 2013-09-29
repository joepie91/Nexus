#!/usr/bin/env python2

import sys

def usage():
	print "Specify a valid action.\nPossible actions: start, stop, add-node, reload-config, reload-packages"

if len(sys.argv) < 2:
	usage()
	exit(1)

if sys.argv[1] == "start":
	import application
	application.run(sys.argv[2:], "blah")
elif sys.argv[1] == "stop":
	pass
else:
	usage()
	exit(1)


"""
parser = argparse.ArgumentParser(description="Nexus control application")

config = core.config.ConfigReader("")
"""
