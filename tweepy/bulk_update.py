'''
author: bobby koteski - 15/04/2017
script reads a large tweet file and pushes the tweets to a 
couchdb database.
'''

import couchdb
import sys, json
from argparse import ArgumentParser

parser = ArgumentParser(description='Processes a JSON tweet file and store in a CouchDB Database')
parser.add_argument('--file', help='JSON file containing tweets to process', required=True)
parser.add_argument('--port', default=5984, help='CouchDB port number (%(default)s)', type=int)
parser.add_argument('--host', help='CouchDB host address (%(default)s)', default='localhost', type=str)
parser.add_argument('--member', help='CouchDB member name', default='', type=str)
parser.add_argument('--pw', help='CouchDB member pw', default='', type=str)
parser.add_argument('--dbname', help='CouchDB database name', required=True, type=str)
parser.add_argument('--debug', help='Print debug messages to screen', action='store_true')
parser.add_argument('--bulk', help='Bulk update number', type=int, default=30000)
args = parser.parse_args()

if args.debug == True: print(args)

if args.member is '':
	server = 'http://' + args.host + ':' + str(args.port) + '/'
else:
	server = 'http://' + args.member + ':' + args.pw + '@' + args.host + ':' + str(args.port) + '/'

if args.debug is True:
	print('Connecting to ', server)

try:
	# db = pycouchdb.Server(server).database(args.dbname)
	db = couchdb.Server(server)[args.dbname]
	if args.debug is True: print('connection successful')
except Exception as e:
	print('Connection unsuccessful')
	sys.exit()

total = 0
docs = []	
with open(args.file) as f:
	for line in f:
		# find the start and end of the json string
		lo = line.find('{')
		hi = line.rfind('}')		
		if lo is not -1 and hi is not -1:
			tweet = json.loads(line[lo:hi+1])['json']
			# get and set the tweet id
			doc = {
				'_id' : tweet['id_str'],
				'text': tweet['text'],
				'lang': tweet['lang']
			}
			# update the rest of the doc with the entire tweet json object
			# strip down tweet
			# doc.update(tweet)
			if args.debug is True:
				print json.dumps(doc,indent=4)
			# add doc to the list of docs
			docs.append(doc)
			# make a bulk insert into the db
			if len(docs) % args.bulk == 0:
				db.update(docs)
				total += len(docs)
				print('updated: ' + str(len(docs)) + ' total: ' + str(total))
				docs = []
	# update the remaining tweets in docs
	if len(docs) > 0:
		db.update(docs)
		total += len(docs)
		print('updated: ' + str(len(docs)) + ' total: ' + str(total))


	
