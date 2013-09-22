import sys
import parser.rulebook

# TODO: Keep trail of message travelling through the rules

f = open(sys.argv[1])
rulebook = f.read()
f.close()

bins = parser.rulebook.parse(rulebook)

class Message(object):
	def __init__(self):
		self.id_ = ""
		self.type_ = "none"
		self.tags = []
		self.source = ""
		self.chain = []
		self.data = {}
		
	def set_data(self, data):
		self.id_ = data['id']
		self.type_ = data['type'] 
		self.tags = data['tags']
		self.source = data['source']
		self.chain = data['chain']
		self.data = data['payload']
		


m = Message()
m.set_data({
	"id": "qwert-yuiop-61238-10842",
	"type": "task",
	"tags": ["convert", "mpeg"],
	"source": "abcde-fghij-00000-00008",
	"chain": ["abcde-fghij-00000-00005", "abcde-fghij-00000-00006"],
	"payload": {
		"command": "convert",
		"category": "video",
		"original_filetype": "mpg"
	}
})

bins['remote'].process(m)
